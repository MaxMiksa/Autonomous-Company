#!/usr/bin/env python3
"""Validate governance headings and compare protected sections without text rewrites."""

from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import os
import re
import sys
import tempfile


HEADINGS = (b"## Human Overrides", b"## Priority Issues")
P1_ITEM = re.compile(
    rb"^([ \t]*)(?:(?:[-+*]|\d+[.)])\s+)?(?:\[([^\]]*)\]\s*)?(?:\*\*|__)?p1(?=\b|__)",
    re.IGNORECASE,
)
LIST_ITEM = re.compile(rb"^([ \t]*)(?:[-+*]|\d+[.)])\s+")


def sections_bytes(data):
    if b"\0" in data:
        raise ValueError("consensus contains NUL bytes")
    lines = data.splitlines(keepends=True)
    starts = {}
    for index, raw in enumerate(lines):
        line = raw.rstrip(b"\r\n")
        normalized = b" ".join(line.strip().rstrip(b"#").strip().split()).lower()
        heading_name = re.sub(rb"^#+\s*", b"", normalized)
        for heading in HEADINGS:
            if line.lstrip().startswith(b"#") and heading_name == heading[3:].lower():
                if line != heading or heading in starts:
                    raise ValueError("governance headings must occur exactly once in canonical form")
                starts[heading] = index
    if len(starts) != len(HEADINGS):
        raise ValueError("consensus requires exactly one Human Overrides and Priority Issues section")
    result = {}
    for heading, start in starts.items():
        end = start + 1
        while end < len(lines) and not re.match(rb"^ {0,3}#{1,2}(?:[ \t]|$)", lines[end]):
            end += 1
        result[heading] = b"".join(lines[start:end])
    return result


def sections(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("consensus must be a regular file")
    return sections_bytes(path.read_bytes())


def p1_items(section):
    """Keep each P1 item and its continuation content as an exact byte record.

    A sibling list item, another P1, or a heading starts the next record. Blank
    separator lines are excluded; indentation and content inside an item are
    preserved. This is the explicit Priority Issues grammar, not a semantic
    classification of arbitrary prose elsewhere in the document.
    """
    lines = section.splitlines(keepends=True)
    for start, line in enumerate(lines[1:], 1):
        match = P1_ITEM.match(line)
        if not match:
            continue
        indent = len(match[1].expandtabs(8))
        end = start + 1
        while end < len(lines):
            following = lines[end]
            sibling = LIST_ITEM.match(following)
            if (P1_ITEM.match(following)
                    or re.match(rb"^ {0,3}#{1,6}(?:[ \t]|$)", following)
                    or (sibling and len(sibling[1].expandtabs(8)) <= indent)):
                break
            end += 1
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        yield b"".join(lines[start:end]), match[2] in (b"x", b"X")


def unresolved_p1(section):
    return any(not resolved for _, resolved in p1_items(section))


def p1_preserved(current, baseline):
    """A cycle may only add unresolved P1s; humans edit the stopped baseline."""
    before = Counter(p1_items(baseline))
    after = Counter(p1_items(current))
    return not (before - after) and not any(resolved for _, resolved in (after - before))


def atomic_write(path, data):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".consensus-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def archive_rejected(path, cycle):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("rejected consensus must be a regular file")
    if not cycle.isdecimal():
        raise ValueError("rejected consensus cycle must be numeric")
    directory = path.parent / "rejected"
    if directory.is_symlink():
        raise ValueError("rejected consensus directory must not be a symlink")
    directory.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    archive = directory / f"consensus-cycle-{int(cycle):04d}-{stamp}-{os.getpid()}.md"
    with archive.open("xb") as stream:
        stream.write(path.read_bytes())
    print(archive)


def reset_consensus(path, template):
    path = Path(path)
    current = sections(path)
    template_data = Path(template).read_bytes()
    for section in sections(template).values():
        template_data = template_data.replace(section, b"", 1)
    # Retain the original order and endings of both human-governed sections.
    replacement = template_data.rstrip(b"\r\n") + b"\n\n" + b"".join(current.values())
    backup_dir = path.parent / "resets"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = backup_dir / f"consensus-before-reset-{stamp}-{os.getpid()}.md"
    with backup.open("xb") as stream:
        stream.write(path.read_bytes())
    atomic_write(path, replacement)
    print(backup)


def main():
    command, path, *extra = sys.argv[1:]
    try:
        if command == "archive-rejected":
            archive_rejected(path, extra[0])
            return 0
        if command == "restore":
            # Validate the saved baseline before restoring; never follow target symlinks.
            sections(extra[0])
            atomic_write(path, Path(extra[0]).read_bytes())
            return 0
        if command == "reset":
            reset_consensus(path, extra[0])
            return 0
        current = sections(path)
        if command == "p1":
            return 0 if unresolved_p1(current[HEADINGS[1]]) else 1
        if command == "unchanged":
            baseline = sections(extra[0])
            return 0 if baseline[HEADINGS[0]] == current[HEADINGS[0]] else 1
        if command == "p1-preserved":
            baseline = sections(extra[0])
            return 0 if p1_preserved(current[HEADINGS[1]], baseline[HEADINGS[1]]) else 1
        if command != "validate":
            raise ValueError("unknown consensus format command")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
