"""Local SQLite persistence. Raw fieldwork is ignored by git."""
import json
import os
from pathlib import Path
import sqlite3
import uuid


DB = Path(os.getenv('RESEARCH_DATA_DIR', 'data')) / 'research.sqlite3'


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
    return c


def save(p):
    p.setdefault('id', uuid.uuid4().hex)
    with connect() as c:
        c.execute('INSERT OR REPLACE INTO projects VALUES (?,?)', (p['id'], json.dumps(p, ensure_ascii=False)))
    return p


def get(pid):
    with connect() as c:
        row = c.execute('SELECT body FROM projects WHERE id=?', (pid,)).fetchone()
    if not row:
        raise ValueError('研究项目不存在')
    return json.loads(row[0])


def listing():
    with connect() as c:
        return [{'id': pid, 'title': json.loads(body)['scope']['title']} for pid, body in c.execute('SELECT id,body FROM projects ORDER BY rowid DESC')]
