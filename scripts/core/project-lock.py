#!/usr/bin/env python3
"""Serialize project operations before taking the separate identity/config locks.

The persistent flock inode is never deleted. Exec and inherited descriptors keep
the lock held while a shell or one of its mutation helpers is still running.
"""

import fcntl
import os
from pathlib import Path
import sys
import tempfile
import time

from product_identity import project_value, safe_path


def rollback_row(root, row):
    """Remove only this creation's unchanged row; preserve later registrations."""
    name, project, _, _ = row.split("\t")
    if project_value(name) != project:
        raise ValueError("Invalid project rollback row")
    if (safe_path(root, project + "/.autonomous-company/identity.json").exists()
            or safe_path(root, ".autonomous-company/product-state.transaction.json").exists()):
        raise ValueError("Registration may be committed or recoverable; retain its source and registry for review")
    registry = safe_path(root, "projects/registry.tsv")
    lines = registry.read_bytes().splitlines(keepends=True)
    matching = [line for line in lines[1:] if line.split(b"\t", 1)[0] == name.encode()]
    expected = row.encode() + b"\n"
    if matching and matching != [expected]:
        raise ValueError("Created project's registry row changed; retain it and its source for review")
    if not matching:
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".registry-rollback.", dir=registry.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(b"".join(line for line in lines if line != expected))
        os.replace(temporary, registry)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    mode, root, *args = sys.argv[1:]
    if mode == "rollback-row":
        rollback_row(root, *args)
        return 0
    if mode != "run":
        raise ValueError("Unknown project lock operation")
    folder = safe_path(root, ".autonomous-company")
    folder.mkdir(exist_ok=True)
    lock = safe_path(root, ".autonomous-company/project-registry.lock")
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    deadline = time.monotonic() + 5
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise ValueError("Another project operation is still running; retry after it completes")
            time.sleep(0.025)
    os.set_inheritable(descriptor, True)
    os.environ["AUTONOMOUS_COMPANY_PROJECT_LOCK_PID"] = str(os.getpid())
    script, *arguments = args
    os.execv("/bin/bash", ["/bin/bash", str(Path(script).resolve()), *arguments])
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        sys.exit(f"Error: {error}")
