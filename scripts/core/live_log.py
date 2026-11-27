"""Private adapter capture mirroring with bounded cross-write redaction."""
from __future__ import annotations

import codecs
import os
from pathlib import Path
import re
import stat
import time

from log_redaction import _secret_values


class StreamRedactor:
    """Keep secret overlap tails; track arbitrarily long Bearer tokens in place."""
    def __init__(self):
        self.values = _secret_values()
        self.maximum = max((len(value) for value in self.values), default=1)
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.buffer = ""
        self.covered = bytearray()
        self.continuing = False
        self.bearer = ""
        self.prefix = ""

    def feed(self, chunk, final=False):
        text = self.decoder.decode(chunk, final=final)
        mask = bytearray(len(text))
        for index, char in enumerate(text):
            if self.bearer == "token":
                if char.isspace():
                    self.bearer = ""
                else:
                    mask[index] = 1
                    continue
            elif self.bearer in ("prefix", "space"):
                if char.isspace():
                    self.bearer = "space"
                    continue
                if self.bearer == "space":
                    self.bearer = "token"
                    mask[index] = 1
                    continue
                self.bearer = ""
            self.prefix = (self.prefix + char)[-6:]
            if re.fullmatch("Bearer", self.prefix, re.IGNORECASE):
                self.bearer = "prefix"
                self.prefix = ""
        self.buffer += text
        self.covered.extend(mask)
        for value in self.values:
            start = 0
            while (start := self.buffer.find(value, start)) >= 0:
                self.covered[start:start + len(value)] = b"\x01" * len(value)
                start += 1
        cutoff = len(self.buffer) if final else max(0, len(self.buffer) - self.maximum + 1)
        result = []
        for index in range(cutoff):
            covered = bool(self.covered[index])
            if covered:
                if not self.continuing:
                    result.append("[REDACTED]")
            else:
                result.append(self.buffer[index])
            self.continuing = covered
        self.buffer, self.covered = self.buffer[cutoff:], self.covered[cutoff:]
        return "".join(result)


def stream_log(root, input_path, relative_path, *, admission, control_path):
    """Mirror only redacted bytes; raw capture stays private to the adapter."""
    root, source = Path(root).resolve(), Path(input_path)
    admission(root)
    cycle = os.environ.get("AUTONOMOUS_COMPANY_CYCLE_ID", "")
    stream_id = cycle
    if os.environ.get("COMPANY_HARNESS_ENABLED") == "1":
        from company_harness import HarnessStore
        attempt_id = os.environ.get("AUTONOMOUS_COMPANY_ATTEMPT_ID", "")
        snapshot = HarnessStore(root).snapshot()
        current = next((c for c in snapshot["cycles"] if c["cycleId"] == cycle), None)
        attempt = next((a for a in current["attempts"] if a["attemptId"] == attempt_id), None) if current else None
        if (not re.fullmatch(r"attempt-[0-9a-f]{32}", attempt_id) or not current
                or current["activeAttemptId"] != attempt_id or not attempt or attempt["status"] != "running"
                or attempt["generation"] != snapshot["generation"]):
            raise ValueError("invalid_stream_identity")
        stream_id = attempt_id
    if not re.fullmatch(r"cycle-[A-Za-z0-9_-]+", cycle) or relative_path != f"logs/{stream_id}.log":
        raise ValueError("invalid_stream_identity")
    directory = source.parent.lstat()
    if not stat.S_ISDIR(directory.st_mode) or source.parent.is_symlink() or directory.st_uid != os.getuid() or directory.st_mode & 0o077:
        raise ValueError("unsafe_stream_directory")
    metadata = source.lstat()
    if source.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_uid != os.getuid():
        raise ValueError("unsafe_stream_capture")
    target = control_path(root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    redactor = StreamRedactor()
    parent = os.getppid()
    completed = source.with_name(source.name + ".complete")
    ready = source.with_name(source.name + ".ready")
    source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    observed = os.fstat(source_fd)
    if (observed.st_dev, observed.st_ino) != (metadata.st_dev, metadata.st_ino) or not stat.S_ISREG(observed.st_mode) or observed.st_uid != os.getuid() or observed.st_nlink != 1:
        os.close(source_fd)
        raise ValueError("stream_capture_changed")
    try:
        target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        observed = os.fstat(target_fd)
        if not stat.S_ISREG(observed.st_mode) or observed.st_uid != os.getuid() or observed.st_nlink != 1:
            os.close(target_fd)
            raise ValueError("unsafe_stream_target")
        os.ftruncate(target_fd, 0)
    except BaseException:
        os.close(source_fd)
        raise
    try:
        with os.fdopen(source_fd, "rb", buffering=0) as capture, os.fdopen(target_fd, "wb", buffering=0) as output:
            ready_fd = os.open(ready, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.write(ready_fd, str(os.getpid()).encode("ascii"))
            os.close(ready_fd)
            while True:
                chunk = capture.read(65536)
                completion = False
                try:
                    done = completed.lstat()
                    if not stat.S_ISREG(done.st_mode) or done.st_uid != os.getuid() or done.st_nlink != 1:
                        raise ValueError("unsafe_stream_completion")
                    completion = True
                except FileNotFoundError:
                    pass
                final = (completion or os.getppid() != parent) and not chunk
                output.write(redactor.feed(chunk, final=final).encode("utf-8"))
                if final:
                    os.fsync(output.fileno())
                    return {"ok": True}
                if not chunk:
                    time.sleep(0.05)
    finally:
        ready.unlink(missing_ok=True)



def stream_log_complete(input_path):
    source = Path(input_path)
    directory = source.parent.lstat()
    if not stat.S_ISDIR(directory.st_mode) or source.parent.is_symlink() or directory.st_uid != os.getuid() or directory.st_mode & 0o077:
        raise ValueError("unsafe_stream_directory")
    complete = source.with_name(source.name + ".complete")
    try:
        descriptor = os.open(complete, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        observed = complete.lstat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_uid != os.getuid() or observed.st_nlink != 1:
            raise ValueError("unsafe_stream_completion")
    else:
        os.close(descriptor)
