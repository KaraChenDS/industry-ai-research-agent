"""Research contracts, portable instruments, sample analysis and report exports."""
import collections
import csv
import datetime
import html
import io
import json
import math
import re


DIMENSIONS = ['使用流程', '决策因素', '行业策略', '用户心理']


def today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()


def instruments(scope):
    return {
        'title': scope['title'] + ' · AI应用行为筛选表',
        'intro': '约5分钟。仅用于研究，自愿参加，可跳过非必填题。请勿填写姓名、客户信息、商业秘密。回答仅保存在你下载的文件里，需由你主动交给研究者。',
        'questions': [
            {'id': 'consent', 'label': '是否同意将以下脱敏回答用于本次调研？', 'type': 'select', 'options': ['同意', '不同意'], 'required': True},
            {'id': 'respondent_id', 'label': '匿名编号（例如团队A-01，不填写真实姓名）', 'type': 'text', 'required': True},
            {'id': 'organization_id', 'label': '团队匿名编号（同团队成员请填写相同编号）', 'type': 'text', 'required': True},
            {'id': 'role', 'label': '你的主要岗位或职责', 'type': 'text', 'required': True},
            {'id': 'team_size', 'label': '团队人数', 'type': 'select', 'options': ['1—4', '5—10', '11—20', '21—50', '51以上'], 'required': True},
            {'id': 'ai_status', 'label': '过去两周，你在工作中使用AI的情况', 'type': 'select', 'options': ['持续使用', '偶尔使用', '尝试后放弃', '未使用'], 'required': True},
            {'id': 'recent_task', 'label': '最近一次具体工作任务是什么？当时需要交付什么？', 'type': 'textarea'},
            {'id': 'workflow', 'label': '从收到任务到交付，依次做了什么？哪些步骤用AI，哪些自己做？', 'type': 'textarea'},
            {'id': 'decision', 'label': '最近一次选择或放弃某个AI工具，主要考虑什么？谁决定购买？', 'type': 'textarea'},
            {'id': 'strategy', 'label': '团队是否有工具、预算、数据使用、验收方面的约定？请举例；没有可填没有。', 'type': 'textarea'},
            {'id': 'psychology', 'label': '最近一次使用或不用AI时，你最在意什么？发生了什么具体情况？', 'type': 'textarea'},
            {'id': 'baseline_min', 'label': '同类任务原来总耗时（分钟，不清楚可留空）', 'type': 'number'},
            {'id': 'ai_total_min', 'label': '使用AI后的全部耗时，含准备、检查、修改（分钟，不清楚可留空）', 'type': 'number'},
            {'id': 'quality_pass', 'label': 'AI辅助后的交付是否达到原有标准？', 'type': 'select', 'options': ['', '是', '否', '不清楚']},
            {'id': 'failure', 'label': '最近一次失败、返工或放弃AI的例子，以及最后如何完成任务', 'type': 'textarea'},
        ],
        'interview': [
            '0—5分钟：确认团队、岗位和近两周任务，选择最近一次具体任务。',
            '5—15分钟：请展示获准使用的脱敏材料，逐步复盘输入、操作、AI交互、人工修改和最终交付。',
            '15—20分钟：追问谁推荐、谁使用、谁采购、谁验收；为什么选择或放弃；比较现有替代办法。',
            '20—25分钟：询问团队预算、协作和数据规则如何影响选择；用具体事件追问担忧与期待，不代替用户解释心理。',
            '25—30分钟：核对总耗时、质量、失败例子；询问能否提供脱敏样例并约下一次任务复测。',
        ],
    }


def plan(scope):
    return [
        {'task': '界定样本边界', 'method': '研究简报', 'hours': 0.5, 'done': '确认地区、团队规模、业务类型、岗位与研究时段', 'status': '待执行'},
        {'task': '搜集通用与行业资料', 'method': '桌面调研', 'hours': 2, 'done': '记录来源、日期、样本口径、适用范围及反例；相同报告不重复算独立证据', 'status': '部分完成' if scope.get('demo') else '待执行'},
        {'task': '分层招募6人', 'method': '目的抽样', 'hours': 1, 'done': '4位一线、1位负责人、1位实施者；覆盖持续使用/放弃/未使用；至少3个团队', 'status': '待执行'},
        {'task': '访谈并观察工作', 'method': '30分钟事件访谈＋脱敏演示', 'hours': 4, 'done': '6份记录，区分口述与直接观察，保留原始证据编号', 'status': '待执行'},
        {'task': '分析场景与反例', 'method': '跨案例对照', 'hours': 1, 'done': '覆盖流程、决策、策略、心理；列出相同任务的成功与失败条件', 'status': '待执行'},
        {'task': '单任务对比验证', 'method': '3—5份真实任务样例', 'hours': 2, 'done': '预先约定质量标准，对比原流程与AI流程全部成本；不外推稳定性', 'status': '待执行'},
    ]


def new_project(title, region='中国大陆（待确认）', segment='5—50人知识工作型创业团队', demo=False):
    scope = {'title': title, 'region': region, 'segment': segment, 'as_of': today(), 'demo': demo,
             'goal': '掌握真实AI应用的使用流程、决策因素、行业策略和用户心理，形成可追溯的场景特征。'}
    return {'scope': scope, 'sources': [], 'scenarios': [], 'plan': plan(scope), 'instruments': instruments(scope),
            'rows': [], 'analysis': analyze_rows([]), 'runs': [], 'interpretation': '尚无足够证据。先搜集公开资料，再用真实工作事件核对。'}


def analyze_rows(rows):
    """Convenience sample descriptions only; blanks stay missing, duplicates rejected."""
    accepted, seen, excluded = [], set(), 0
    for row in rows:
        if row.get('consent') != '同意':
            excluded += 1
            continue
        rid = str(row.get('respondent_id', '')).strip()
        if not rid:
            raise ValueError('同意参与的回答必须有匿名 respondent_id')
        if rid in seen:
            raise ValueError('匿名编号重复：' + rid)
        seen.add(rid)
        accepted.append(row)
    statuses = collections.Counter(r.get('ai_status') or '缺失' for r in accepted)
    orgs = {r['organization_id'] for r in accepted if r.get('organization_id')}
    savings = []
    for r in accepted:
        a, b = r.get('baseline_min'), r.get('ai_total_min')
        if a in (None, '') or b in (None, ''):
            continue
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            raise ValueError('耗时必须为有限的非负数字')
        if not math.isfinite(a) or not math.isfinite(b) or a < 0 or b < 0:
            raise ValueError('耗时必须为有限的非负数字')
        if r.get('quality_pass') == '是':
            savings.append(a - b)
    return {'n': len(accepted), 'organizations': len(orgs), 'excluded_no_consent': excluded,
            'status_counts': dict(statuses), 'status_denominator': len(accepted),
            'paired_quality_pass_n': len(savings),
            'mean_saved_minutes': round(sum(savings) / len(savings), 2) if savings else None,
            'limits': '自愿参与的便利样本；按受访者统计使用状态，非企业渗透率。耗时为自报配对数据，仅纳入质量达标且两项耗时完整的回答；不证明因果关系或行业ROI。'}


def parse_dataset(text):
    if text.lstrip().startswith(('[', '{')):
        obj = json.loads(text)
        rows = obj if isinstance(obj, list) else [obj]
    else:
        rows = list(csv.DictReader(io.StringIO(text.lstrip('\ufeff'))))
    if len(rows) > 10000 or any(not isinstance(r, dict) for r in rows):
        raise ValueError('仅接受不超过10000行的CSV或JSON回答对象')
    analyze_rows(rows)
    return rows


def validate_artifacts(artifacts, sources):
    """Enforce provenance existence, not semantic entailment (human review required)."""
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get('scenarios'), list):
        raise ValueError('模型输出需包含 scenarios 数组')
    known = {s['id']: s for s in sources}
    for s in artifacts['scenarios']:
        if not isinstance(s, dict):
            raise ValueError('场景必须为对象')
        for key in ['name', 'role', 'trigger', 'workflow', 'decision', 'strategy', 'psychology', 'counterexample', 'next_step', 'evidence_ids']:
            if key not in s:
                raise ValueError('场景缺少字段：' + key)
        if not isinstance(s['workflow'], list) or not isinstance(s['evidence_ids'], list):
            raise ValueError('workflow / evidence_ids 必须为数组')
        if any(not isinstance(ref, str) or ref not in known for ref in s['evidence_ids']):
            raise ValueError('场景引用了不存在的证据编号')
        for key in ['name', 'role', 'trigger', 'decision', 'strategy', 'psychology', 'counterexample', 'next_step']:
            if not isinstance(s[key], str):
                raise ValueError('场景文本字段无效：' + key)
        if any(not isinstance(step, str) for step in s['workflow']):
            raise ValueError('流程步骤必须为字符串')
        direct = [known[ref] for ref in s['evidence_ids'] if known[ref]['kind'] in ['interview', 'observation', 'survey_response']]
        s['status'] = '有一手材料，待人工核对支持关系' if direct else '待验证假设'
        s['psychology_status'] = '用户心理解释仍需具体事件及本人表述核对'
    if not isinstance(artifacts.get('interpretation'), str):
        raise ValueError('模型输出需包含 interpretation 字符串')
    if any(ref not in known for ref in re.findall(r'\[(S\d+)\]', artifacts['interpretation'])):
        raise ValueError('现状解读引用了不存在的证据编号')
    return artifacts


def report(project):
    p, out = project, []
    scope = p['scope']
    out += ['# ' + scope['title'] + ' · AI应用现状研究', '',
            '**研究状态：探索性研究；公开资料＋待验证假设，不是行业代表性调查。**', '',
            f"范围：{scope['region']}；{scope['segment']}。资料截止：{scope['as_of']}。", '',
            '## 现状解读', '', p['interpretation'], '',
            '来源编号可追溯不等于来源支持全部推断；请逐条人工核对。心理、策略和场景推断均应寻找反例。', '',
            '## 研究计划', '']
    for t in p['plan']:
        out += [f"- {t['task']}｜{t['method']}｜{t['hours']}小时｜{t['status']}。完成标准：{t['done']}"]
    out += ['', '## 场景特征与待核实问题', '']
    for s in p['scenarios']:
        out += ['### ' + s['name'], '', f"状态：{s['status']}。证据：{', '.join(s['evidence_ids']) or '无'}。", '',
                f"岗位：{s['role']}；触发：{s['trigger']}", '', '流程：' + ' → '.join(s['workflow']), '',
                '决策因素：' + s['decision'], '', '行业/组织策略：' + s['strategy'], '',
                '用户心理（待核实）：' + s['psychology'], '', '反例/边界：' + s['counterexample'], '', '下一步：' + s['next_step'], '']
    out += ['## 自采样本分析', '', '```json', json.dumps(p['analysis'], ensure_ascii=False, indent=2), '```', '',
            '## 访谈提纲', '']
    out += ['- ' + q for q in p['instruments']['interview']]
    out += ['', '## 问卷字段', '']
    out += [f"- {q['id']}：{q['label']}" for q in p['instruments']['questions']]
    out += ['', '## 证据来源', '']
    for s in p['sources']:
        out += [f"### [{s['id']}] {s['title']}", '', f"类型：{s['kind']}；日期：{s['date']}；采集：{s.get('accessed', '未记录')}；范围：{s['population']}", '',
                s['note'], '', '边界：' + s['limits'], '', s.get('url', ''), '']
    out += ['## 研究局限与下一轮', '',
            '公开资料可能来自不同地区、年份、样本及AI定义，不能直接比较比例。厂商工具使用日志不等于企业采用率。', '',
            '没有真实受访者时，不能确认目标群体使用习惯、购买动机、心理与业务收益。补充持续使用、放弃和未使用者的对照；用脱敏真实任务检验质量与全部成本。', '',
            '## Agent运行记录', '']
    for r in p['runs']:
        out += [f"- {r['at']}｜{r['mode']}｜{r.get('phase', '')}｜{r['status']}"]
    return '\n'.join(out)


def report_html(project):
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>研究报告</title><style>body{max-width:900px;margin:60px auto;padding:24px;color:#24372e;font:16px/1.9 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}button{padding:10px}@media print{button{display:none}}</style><button onclick="print()">打印 / 保存PDF</button><pre>' + html.escape(report(project)) + '</pre></html>'


def form_html(instrument):
    schema = json.dumps(instrument, ensure_ascii=False).replace('<', '\\u003c')
    return '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AI应用研究问卷</title><style>body{max-width:720px;margin:40px auto;padding:24px;background:#f5f6f0;color:#253e32;font:16px/1.8 system-ui}label{display:block;margin-top:24px}input,textarea,select{box-sizing:border-box;display:block;width:100%;padding:12px;border:1px solid #b7c2b7;border-radius:8px;background:white}button{margin-top:30px;padding:14px;background:#294e3b;color:white;border:0;border-radius:8px}</style><h1></h1><p></p><form></form><script>
const schema=SCHEMA;document.querySelector('h1').textContent=schema.title;document.querySelector('p').textContent=schema.intro;
const form=document.querySelector('form');for(const q of schema.questions){const label=document.createElement('label');label.textContent=q.label+(q.required?' *':'');const el=document.createElement(q.type==='select'?'select':q.type==='textarea'?'textarea':'input');el.name=q.id;el.required=!!q.required;if(q.type==='select'){const empty=document.createElement('option');empty.value='';empty.textContent='请选择';el.append(empty);for(const v of q.options){const op=document.createElement('option');op.value=v;op.textContent=v;el.append(op)}}else if(q.type!=='textarea'){el.type=q.type; if(q.type==='number'){el.min=0;el.step='any'}}label.append(el);form.append(label)}const b=document.createElement('button');b.textContent='下载我的回答，主动交给研究者';form.append(b);form.onsubmit=e=>{e.preventDefault();const data=Object.fromEntries(new FormData(form));if(data.consent!=='同意'){alert('未同意参加，不生成研究回答文件。');return}const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));a.download='research-response.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
</script></html>'''.replace('SCHEMA', schema)
