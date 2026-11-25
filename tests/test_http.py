"""Exercise real handlers without binding a network port (sandbox compatible)."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import Handler
from research import store
from research.demo import demo_project


class MemoryHandler(Handler):
    def __init__(self, path, data=None, origin='http://localhost:8765'):
        self.path = path
        raw = json.dumps(data).encode() if data is not None else b''
        self.headers = {'Host': 'localhost:8765', 'Origin': origin, 'Content-Length': str(len(raw))}
        self.rfile, self.wfile = io.BytesIO(raw), io.BytesIO()
        self.sent = None

    def send(self, body, content_type='application/json', status=200, filename=None):
        self.sent = (body, status, content_type, filename)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patcher = patch.object(store, 'DB', Path(self.tmp.name) / 'http.sqlite3')
        self.patcher.start()
        self.project = store.save(demo_project())

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def post(self, path, data):
        h = MemoryHandler(path, {'id': self.project['id'], **data})
        h.do_POST()
        return h.sent

    def test_state_and_all_exports(self):
        h = MemoryHandler('/api/state')
        h.do_GET()
        self.assertEqual(h.sent[0]['project']['id'], self.project['id'])
        for kind in ['form', 'report', 'report-html', 'project']:
            h = MemoryHandler('/api/export/' + kind + '?id=' + self.project['id'])
            h.do_GET()
            self.assertEqual(h.sent[1], 200)
            self.assertTrue(h.sent[3])

    def test_response_roundtrip_and_qualitative_evidence(self):
        rows = [{'consent': '同意', 'respondent_id': 'test-A-01', 'organization_id': 'test-A',
                 'ai_status': '持续使用', 'workflow': '测试记录，不是真实访谈', 'baseline_min': 40,
                 'ai_total_min': 25, 'quality_pass': '是'}, {'consent': '不同意', 'private': 'MUST_NOT_STORE'}]
        body, status, _, _ = self.post('/api/data', {'text': json.dumps(rows)})
        self.assertEqual(status, 200)
        p = body['project']
        self.assertEqual(p['analysis']['mean_saved_minutes'], 15)
        self.assertEqual(p['sources'][-1]['kind'], 'survey_response')
        self.assertNotIn('MUST_NOT_STORE', json.dumps(store.get(p['id'])))
        self.assertEqual(self.post('/api/data', {'text': json.dumps(rows)})[1], 400)
        self.assertEqual(len(store.get(p['id'])['rows']), 1)

    def test_new_project_isolated_and_source_saved(self):
        body, status, _, _ = self.post('/api/new', {'title': '测试行业', 'region': '测试地区', 'segment': '测试岗位'})
        self.assertEqual(status, 200)
        self.assertEqual(body['project']['sources'], [])
        self.assertNotEqual(body['project']['id'], self.project['id'])
        source = {'kind': 'interview', 'title': 'test-only', 'date': '未核实', 'url': '',
                  'note': '仅用于测试', 'population': '测试数据', 'limits': '非真实访谈'}
        body, status, _, _ = self.post('/api/source', {'source': source})
        self.assertEqual(status, 200)
        self.assertEqual(body['project']['sources'][-1]['id'], 'S5')

    def test_unauthorized_origin_host_and_unsafe_links(self):
        h = MemoryHandler('/api/new', {}, 'https://untrusted.invalid')
        h.do_POST()
        self.assertEqual(h.sent[1], 403)
        h = MemoryHandler('/api/state')
        h.headers['Host'] = 'untrusted.invalid'
        h.do_GET()
        self.assertEqual(h.sent[1], 403)
        body, status, _, _ = self.post('/api/source', {'source': {'kind': 'public_research', 'title': 'test', 'note': 'test', 'url': 'javascript:alert(1)'}})
        self.assertEqual(status, 400)

    def test_real_model_requires_explicit_external_processing_consent(self):
        self.assertEqual(self.post('/api/agent', {'phase': '综合研究报告', 'consent_external': False})[1], 400)


if __name__ == '__main__':
    unittest.main()
