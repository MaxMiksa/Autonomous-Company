"""Reject pre-v3 writable state; migration is explicit and never dual-write."""
import argparse
import os
from pathlib import Path


def check_environment(environ=None):
    environ = os.environ if environ is None else environ
    old = sorted(key for key in environ if key.startswith('AUTO_COMPANY_'))
    if old:
        raise ValueError('Legacy environment names require one-time migration: ' + ', '.join(old))


def check_root(root, environ=None):
    check_environment(environ)
    root = Path(root)
    if (root / '.autonomous-company-migration-in-progress.json').exists():
        raise ValueError('Namespace migration is in progress; complete or roll it back before starting')
    old = sorted(path.name for path in root.glob('.auto-company*'))
    if old:
        raise ValueError('Old Auto-Company state requires scripts/migrate-name.py before use: ' + ', '.join(old))
    for name in ('.auto-loop.env', '.autonomous-company.local'):
        path = root / name
        if path.is_file():
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.startswith('AUTO_COMPANY_'):
                    raise ValueError('Legacy configuration key requires one-time migration in ' + name)


def check_center(data_dir):
    """Run before CenterStore can create a directory or center identity."""
    check_environment()
    path = Path(data_dir)
    if (path / '.autonomous-company-migration-in-progress.json').exists():
        raise ValueError('Center namespace migration is in progress; complete or roll it back before starting')
    parts = path.parts
    for index, part in enumerate(parts):
        if part in {'AutoCompany', 'auto-company'}:
            raise ValueError('Old center directory requires one-time migration before use')
        old = {'AutonomousCompany': 'AutoCompany', 'autonomous-company': 'auto-company'}.get(part)
        if old:
            previous = Path(*parts[:index], old, *parts[index + 1:])
            if previous.exists():
                raise ValueError('Old center data exists; migrate it before creating or opening this center: ' + str(previous))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        check_root(args.root)
    except ValueError as error:
        parser.exit(78, str(error) + '\n')
