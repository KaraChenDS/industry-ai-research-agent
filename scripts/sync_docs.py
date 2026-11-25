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
    parser.add_argument('--source', type=Path, help='private source directory outside this public repository')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    settings_path = ROOT / '.obsidian-sync.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    target_value = args.target or settings.get('target')
    source_value = args.source or settings.get('source')
    if not target_value or not source_value:
        parser.error('Configure explicit private source and target directories; project documents must stay outside the public repository.')
    target = Path(target_value)
    source = Path(source_value).expanduser().resolve()
    if source == ROOT or ROOT in source.parents:
        parser.error('Private source must be outside the public repository.')
    target = target.expanduser().resolve()
    if not args.check:
        target.mkdir(parents=True, exist_ok=True)
    failed = []
    for source_name, destination_name in FILES.items():
        contents = (source / source_name).read_bytes()
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
