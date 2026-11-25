import copy
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from research import agent, store
from research.demo import demo_project
from research.domain import analyze_rows, form_html, new_project, parse_dataset, report_html, validate_artifacts


def response(rid='A-01', **kw):
    return dict(consent='同意', respondent_id=rid, organization_id='A', ai_status='持续使用', **kw)


class ResearchTests(unittest.TestCase):
    def test_demo_has_no_fabricated_fieldwork(self):
        p = demo_project()
        self.assertEqual(p['analysis']['n'], 0)
        self.assertEqual(p['rows'], [])
        self.assertTrue(all(s['status'] == '待验证假设' for s in p['scenarios']))
        self.assertFalse(any(s['kind'] in ['interview', 'observation'] for s in p['sources']))

    def test_new_industry_has_no_startup_findings(self):
        p = new_project('宠物用品零售', '上海', '小型零售门店')
        self.assertEqual(p['sources'], [])
        self.assertEqual(p['scenarios'], [])

    def test_no_consent_is_excluded_and_duplicates_rejected(self):
        self.assertEqual(analyze_rows([{'consent': '不同意'}])['n'], 0)
        with self.assertRaises(ValueError):
            analyze_rows([response(), response()])

    def test_correct_denominator_missing_and_quality(self):
        rows = [response(baseline_min='40', ai_total_min='25', quality_pass='是'),
                response('A-02', baseline_min='', ai_total_min='0', quality_pass='是'),
                response('A-03', baseline_min='40', ai_total_min='5', quality_pass='否')]
        a = analyze_rows(rows)
        self.assertEqual((a['n'], a['organizations'], a['paired_quality_pass_n']), (3, 1, 1))
        self.assertEqual(a['mean_saved_minutes'], 15)

    def test_negative_savings_preserved(self):
        self.assertEqual(analyze_rows([response(baseline_min='20', ai_total_min='30', quality_pass='是')])['mean_saved_minutes'], -10)

    def test_nonfinite_and_negative_times_rejected(self):
        for value in ['NaN', 'inf', '-2', 'abc']:
            with self.assertRaises(ValueError):
                analyze_rows([response(baseline_min=value, ai_total_min=1, quality_pass='是')])

    def test_csv_json_equivalence(self):
        csv = 'consent,respondent_id,organization_id,ai_status\n同意,A-01,A,持续使用\n'
        self.assertEqual(analyze_rows(parse_dataset(csv)), analyze_rows(parse_dataset(json.dumps(response()))))

    def test_unknown_citation_rejected_and_certainty_downgraded(self):
        p = demo_project()
        a = {'scenarios': copy.deepcopy(p['scenarios']), 'interpretation': '背景[S1]'}
        a['scenarios'][0]['status'] = '已确认'
        self.assertEqual(validate_artifacts(a, p['sources'])['scenarios'][0]['status'], '待验证假设')
        a['scenarios'][0]['evidence_ids'] = ['S999']
        with self.assertRaises(ValueError):
            validate_artifacts(a, p['sources'])
        a['scenarios'] = []
        a['interpretation'] = '背景[S999]'
        with self.assertRaises(ValueError):
            validate_artifacts(a, p['sources'])

    def test_report_and_form_escape_untrusted_content(self):
        p = demo_project()
        p['interpretation'] = '<script>alert(1)</script>'
        p['instruments']['title'] = '</script><script>alert(2)</script>'
        self.assertNotIn('<script>alert(1)', report_html(p))
        self.assertNotIn('</script><script>alert(2)', form_html(p['instruments']))

    def test_store_roundtrip_and_nonexistent(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory, patch.object(store, 'DB', Path(directory) / 'test.sqlite3'):
            p = store.save(demo_project())
            self.assertEqual(store.get(p['id']), p)
            with self.assertRaises(ValueError):
                store.get('nonexistent')

    @patch.dict(os.environ, {'LLM_API_KEY': 'unit-test-not-real', 'LLM_BASE_URL': 'https://model.invalid', 'LLM_MODEL': 'test-model', 'AGENT_MAX_ROUNDS': '4', 'TAVILY_API_KEY': ''})
    def test_actual_model_tool_loop_with_mock_transport(self):
        p = demo_project()
        artifact = {k: p[k] for k in ['interpretation', 'scenarios', 'plan', 'instruments']}
        payloads = []
        def fake(url, payload, headers=None):
            payloads.append(copy.deepcopy(payload))
            if len(payloads) == 1:
                msg = {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'call1', 'type': 'function', 'function': {'name': 'analyze_dataset', 'arguments': '{}'}}]}
            else:
                msg = {'role': 'assistant', 'content': json.dumps(artifact, ensure_ascii=False)}
            return {'choices': [{'message': msg}]}
        result = agent.run(p, '行业数据分析', fake)
        self.assertEqual(result['runs'][0]['trace'][0]['tool'], 'analyze_dataset')
        self.assertEqual(payloads[1]['messages'][-1]['role'], 'tool')
        self.assertEqual(result['analysis']['n'], 0)

    @patch.dict(os.environ, {'LLM_API_KEY': ''})
    def test_live_agent_does_not_silently_fake_results(self):
        with self.assertRaises(ValueError):
            agent.run(demo_project(), '综合研究报告')

    @patch.dict(os.environ, {'LLM_API_KEY': 'unit-test', 'LLM_BASE_URL': 'https://model.invalid', 'LLM_MODEL': 'test-model', 'AGENT_MAX_ROUNDS': '1', 'TAVILY_API_KEY': ''})
    def test_round_budget_stops_unfinished_agent(self):
        def fake(url, payload, headers=None):
            return {'choices': [{'message': {'role': 'assistant', 'content': None, 'tool_calls': [
                {'id': 'c', 'type': 'function', 'function': {'name': 'inspect_evidence', 'arguments': '{"query":""}'}}]}}]}
        with self.assertRaisesRegex(ValueError, '轮次上限'):
            agent.run(demo_project(), '综合研究报告', fake)

    @patch.dict(os.environ, {'LLM_API_KEY': 'unit-test', 'LLM_BASE_URL': 'https://model.invalid', 'LLM_MODEL': 'test-model', 'AGENT_MAX_ROUNDS': '3', 'TAVILY_API_KEY': 'unit-test', 'AGENT_SEARCH_BUDGET': '1'})
    def test_search_budget_and_unverified_provenance(self):
        p = demo_project()
        searches, turns = [], []
        artifact = {k: p[k] for k in ['interpretation', 'scenarios', 'plan', 'instruments']}
        def fake(url, payload, headers=None):
            if 'tavily' in url:
                searches.append(payload)
                return {'results': [{'title': 'Test source', 'url': 'https://example.org/test', 'content': 'synthetic test excerpt'}]}
            turns.append(payload)
            if len(turns) == 1:
                calls = [{'id': str(i), 'type': 'function', 'function': {'name': 'search_public_evidence', 'arguments': '{"query":"test"}'}} for i in range(2)]
                return {'choices': [{'message': {'role': 'assistant', 'content': None, 'tool_calls': calls}}]}
            return {'choices': [{'message': {'role': 'assistant', 'content': json.dumps(artifact)}}]}
        out = agent.run(p, '现状解读与场景特征', fake)
        self.assertEqual(len(searches), 1)
        self.assertEqual(out['sources'][-1]['kind'], 'search_excerpt')
        self.assertEqual(out['runs'][-1]['searches'], 1)


if __name__ == '__main__':
    unittest.main()
