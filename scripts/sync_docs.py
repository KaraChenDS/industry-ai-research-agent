#!/usr/bin/env python3
"""Sync canonical project documents to an explicitly configured local folder."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = {'product-requirements.md': '行业调研Agent_产品需求文档.md',
         'agent-strategy.md': '行业调研Agent_策略设计文档.md',
         'whitepaper.md': '行业调研Agent_白皮书.md'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = args.target
    if target is None:
        settings = ROOT / '.obsidian-sync.json'
        if not settings.exists():
            parser.error('Pass --target or configure .obsidian-sync.json with a target path.')
        target = Path(json.loads(settings.read_text())['target'])
    target = target.expanduser().resolve()
    if not args.check:
        target.mkdir(parents=True, exist_ok=True)
    failed = []
    for source_name, destination_name in FILES.items():
        contents = (ROOT / 'docs' / source_name).read_bytes()
        destination = target / destination_name
        matches = destination.is_file() and destination.read_bytes() == contents
        if not matches and args.check:
            failed.append(destination_name)
            continue
        if not matches:
            fd, path = tempfile.mkstemp(prefix='.fieldnote-', dir=str(target))
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(contents)
                os.replace(path, destination)
            finally:
                Path(path).unlink(missing_ok=True)
        print(destination_name + ' · ' + hashlib.sha256(contents).hexdigest()[:12])
    if failed:
        raise SystemExit('Out of sync: ' + ', '.join(failed))


if __name__ == '__main__':
    main()
