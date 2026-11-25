#!/usr/bin/env python3
"""Local research workbench. Run: python3 app.py. No third-party dependencies."""
import argparse
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from research import agent, store
from research.demo import demo_project
from research.domain import analyze_rows, form_html, new_project, parse_dataset, report, report_html, today

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
LOCK = threading.Lock()


def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class Handler(BaseHTTPRequestHandler):
    def send(self, body, content_type='application/json; charset=utf-8', status=200, filename=None):
        if not isinstance(body, (str, bytes)):
            body = json.dumps(body, ensure_ascii=False)
        body = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get('Host', '').split(':')[0] not in ['localhost', '127.0.0.1']:
            return self.send({'error': '仅允许本机访问'}, status=403)
        try:
            url = urlsplit(self.path)
            if url.path == '/api/state':
                projects = store.listing()
                pid = parse_qs(url.query).get('id', [projects[0]['id'] if projects else ''])[0]
                return self.send({'project': store.get(pid), 'projects': projects, 'config': agent.config()})
            if url.path.startswith('/api/export/'):
                p = store.get(parse_qs(url.query)['id'][0])
                kind = url.path.rsplit('/', 1)[1]
                if kind == 'form':
                    return self.send(form_html(p['instruments']), 'text/html; charset=utf-8', filename='research-form.html')
                if kind == 'report-html':
                    return self.send(report_html(p), 'text/html; charset=utf-8', filename='research-report.html')
                if kind == 'report':
                    return self.send(report(p), 'text/markdown; charset=utf-8', filename='research-report.md')
                if kind == 'project':
                    return self.send(p, filename='research-project-private.json')
                raise ValueError('未知导出类型')
            path = (ROOT / 'web' / url.path.lstrip('/')).resolve() if url.path != '/' else ROOT / 'web/index.html'
            if not path.is_relative_to(ROOT / 'web') or not path.is_file():
                return self.send({'error': '未找到'}, status=404)
            types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json'}
            return self.send(path.read_bytes(), types.get(path.suffix, 'application/octet-stream') + '; charset=utf-8')
        except (ValueError, KeyError, IndexError) as e:
            self.send({'error': str(e)}, status=400)

    def do_POST(self):
        # Loopback-only service; reject browser cross-site requests.
        if self.headers.get('Origin') and self.headers['Origin'] != 'http://' + self.headers.get('Host', ''):
            return self.send({'error': '不允许跨站写入'}, status=403)
        if self.headers.get('Host', '').split(':')[0] not in ['localhost', '127.0.0.1']:
            return self.send({'error': '仅允许本机访问'}, status=403)
        if not LOCK.acquire(blocking=False):
            return self.send({'error': '另一项保存或Agent任务正在执行，请稍后再试'}, status=409)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size > 2_000_000:
                raise ValueError('请求过大；请控制在2MB以内')
            body = json.loads(self.rfile.read(size))
            path = urlsplit(self.path).path
            if path == '/api/new':
                p = demo_project() if body.get('demo') else new_project(str(body['title'])[:150], str(body.get('region', '待确认'))[:150], str(body.get('segment', '待确认'))[:300])
            else:
                p = store.get(body['id'])
                if path == '/api/source':
                    s = body['source']
                    if s['kind'] not in ['public_research', 'vendor_research', 'interview', 'observation', 'method']:
                        raise ValueError('未知证据类型')
                    if not s.get('title', '').strip() or not s.get('note', '').strip():
                        raise ValueError('请填写标题和脱敏证据内容')
                    if s.get('url') and urlsplit(s['url']).scheme not in ['http', 'https']:
                        raise ValueError('来源链接仅支持http/https')
                    s['id'], s['accessed'] = 'S' + str(len(p['sources']) + 1), today()
                    p['sources'].append(s)
                elif path == '/api/data':
                    rows = parse_dataset(body['text'])
                    # Append unique responses; no-consent answers are not stored.
                    rows = [r for r in rows if r.get('consent') == '同意']
                    candidate = p['rows'] + rows
                    p['analysis'] = analyze_rows(candidate)
                    p['rows'] = candidate
                    for row in rows:
                        p['sources'].append({'id': 'S' + str(len(p['sources']) + 1),
                            'title': '问卷回答 · ' + str(row['respondent_id']), 'kind': 'survey_response',
                            'date': today(), 'accessed': today(), 'url': '',
                            'population': '匿名团队 ' + str(row.get('organization_id', '缺失')) + '；' + str(row.get('role', '岗位未填')),
                            'note': json.dumps(row, ensure_ascii=False),
                            'limits': '同意参与的脱敏自报回答；未直接观察，不能直接确认因果关系、心理动机或行业总体。'})
                elif path == '/api/agent':
                    phases = ['调研方法与任务拆分', '现状解读与场景特征', '行业数据分析', '问卷与访谈材料生成', '综合研究报告']
                    if body['phase'] not in phases:
                        raise ValueError('未知研究阶段')
                    if not body.get('consent_external'):
                        raise ValueError('运行前需确认将项目中的脱敏材料发送给配置的模型服务')
                    p = agent.run(p, body['phase'])
                else:
                    raise ValueError('未知操作')
            store.save(p)
            self.send({'project': p, 'projects': store.listing(), 'config': agent.config()})
        except (ValueError, KeyError, TypeError) as e:
            self.send({'error': str(e)[:500]}, status=400)
        except Exception:
            self.send({'error': '执行失败，未保存本轮结果。请检查服务配置或输入格式。'}, status=500)
        finally:
            LOCK.release()

    def log_message(self, format, *args):
        # Do not log fieldwork bodies, keys or prompts.
        pass


if __name__ == '__main__':
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not store.listing():
        store.save(demo_project())
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print('Fieldnote is running: http://127.0.0.1:' + str(args.port), flush=True)
    server.serve_forever()
