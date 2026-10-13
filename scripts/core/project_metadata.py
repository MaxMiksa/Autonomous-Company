"""Small, identity-bound product descriptions. Never infer them from consensus."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

LIMIT = 4096
FILENAME = ".autonomous-company-project.json"
KEYS = {"version", "project", "displayName", "description", "recordedAt", "source"}


def validate(value, project):
    if not isinstance(value, dict) or set(value) != KEYS:
        raise ValueError("Unexpected project metadata fields")
    if type(value["version"]) is not int or value["version"] != 1 or value["project"] != project:
        raise ValueError("Project metadata identity does not match")
    if not isinstance(project, str) or not re.fullmatch(r"projects/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", project):
        raise ValueError("Explicit project identity required")
    if value["source"] != "project_metadata":
        raise ValueError("Invalid project metadata source")
    for key, limit in (("displayName", 80), ("description", 300)):
        text = value[key]
        if not isinstance(text, str) or text != text.strip() or len(text) > limit or any(ord(c) < 32 for c in text):
            raise ValueError(f"Invalid {key}")
    if not value["displayName"]:
        raise ValueError("Display name is required")
    if not isinstance(value["recordedAt"], str) or datetime.fromisoformat(value["recordedAt"]).tzinfo is None:
        raise ValueError("Metadata timestamp needs a timezone")
    return value


def metadata_path(root, project):
    if not isinstance(project, str) or not re.fullmatch(r"projects/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", project):
        raise ValueError("Explicit project identity required")
    root = Path(root).resolve()
    path = root
    for part in (*project.split("/"), FILENAME):
        path /= part
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("Linked metadata paths are unsupported")
    path.resolve().relative_to(root)
    return path


def read_metadata(root, project):
    path = metadata_path(root, project)
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > LIMIT:
        raise ValueError("Metadata must be a bounded regular file")
    return validate(json.loads(path.read_text(encoding="utf-8")), project)


def write_metadata(root, project, display_name, description):
    path = metadata_path(root, project)
    if not path.parent.is_dir():
        raise ValueError("Project does not exist")
    value = validate({"version": 1, "project": project, "displayName": display_name,
                      "description": description, "recordedAt": datetime.now(timezone.utc).isoformat(),
                      "source": "project_metadata"}, project)
    descriptor, temporary = tempfile.mkstemp(prefix=".project-metadata-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=os.environ.get("AUTONOMOUS_COMPANY_ROOT") or Path(__file__).resolve().parents[2])
    parser.add_argument("--project", default=os.environ.get("ACTIVE_PROJECT"))
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--description", default="")
    args = parser.parse_args()
    try:
        write_metadata(args.root, args.project, args.display_name, args.description)
    except (OSError, ValueError, TypeError) as error:
        print(f"Project metadata: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
