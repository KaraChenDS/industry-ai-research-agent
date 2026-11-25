#!/usr/bin/env python3
"""Build a shareable static preview exclusively from curated public seed data."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.demo import demo_project
from research.domain import form_html, report, report_html

p = demo_project()
p['id'] = 'startup-office-public-demo'
state = {'project': p, 'projects': [{'id': p['id'], 'title': p['scope']['title']}],
         'config': {'model_configured': False, 'search_configured': False, 'model': '', 'max_rounds': 6, 'search_budget': 3}}
target = ROOT / 'docs'
target.mkdir(exist_ok=True)
for name in ['index.html', 'style.css', 'app.js']:
    shutil.copyfile(ROOT / 'web' / name, target / name)
page = (ROOT / 'web/index.html').read_text()
page = page.replace('<link rel="stylesheet" href="style.css">', '<style>' + (ROOT / 'web/style.css').read_text() + '</style>')
script = 'window.FIELDNOTE_DEMO_STATE=' + json.dumps(state, ensure_ascii=False).replace('<', '\\u003c') + ';\n' + (ROOT / 'web/app.js').read_text()
page = page.replace('<script src="app.js"></script>', '<script>' + script + '</script>')
(target / 'index.html').write_text(page)
(target / 'demo-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2))
(target / 'demo-report.md').write_text(report(p))
(target / 'demo-report.html').write_text(report_html(p))
(target / 'demo-form.html').write_text(form_html(p['instruments']))
(target / '.nojekyll').touch()
print('Built public preview from curated seed only; 0 interviews, 0 responses.')
