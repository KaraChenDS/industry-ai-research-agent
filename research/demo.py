"""Curated public evidence, with explicit population limits. No invented interviews."""
from .domain import new_project, today


def demo_project():
    p = new_project('小型创业公司办公场景', demo=True)
    p['sources'] = [
        {'id': 'S1', 'title': 'OECD · Generative AI and the SME Workforce', 'kind': 'public_research', 'date': '2025-11-05', 'accessed': today(),
         'url': 'https://www.oecd.org/en/publications/generative-ai-and-the-sme-workforce_2d08b99d-en/full-report/component-4.html',
         'population': 'OECD所调查地区的中小企业；并非中国创业公司办公专项样本',
         'note': '调查显示生成式AI已用于部分中小企业，知识、专业及行政工作是值得进一步考察的方向。',
         'limits': '只能用于提出任务线索；不能证明本研究目标人群的采用率和使用流程。'},
        {'id': 'S2', 'title': 'U.S. Chamber · 2026 Empowering Small Business Report', 'kind': 'public_research', 'date': '2026-10-02', 'accessed': today(),
         'url': 'https://www.uschamber.com/technology/2026-empowering-small-business-report',
         'population': '美国小企业；网页摘要，完整抽样及AI定义需进一步核对',
         'note': '发布方摘要称66%的美国小企业使用AI。此数字仅作为该报告口径下的背景，不作为中国5—50人创业团队的数据。',
         'limits': '美国小企业不等于创业公司；摘要不能替代方法审查；相关性不能证明AI导致增长。'},
        {'id': 'S3', 'title': 'Anthropic Economic Index · Software development', 'kind': 'vendor_research', 'date': '2025-04-28', 'accessed': today(),
         'url': 'https://www.anthropic.com/research/impact-software-development',
         'population': 'Claude.ai与Claude Code编码相关交互；分析单位是对话，不是企业',
         'note': '厂商研究观察到编码任务中的自动化与协作方式差异，并对创业相关工作作初步分类。',
         'limits': '单厂商、编码任务、对话样本；不能推断所有创业团队或所有办公任务的使用比例。'},
        {'id': 'S4', 'title': 'GOV.UK · Contextual research and observation', 'kind': 'method', 'date': '未标注', 'accessed': today(),
         'url': 'https://www.gov.uk/service-manual/user-research/contextual-research-and-observation',
         'population': '用户研究方法，不是AI采用情况调查',
         'note': '建议观察人们在熟悉环境中，使用自己的设备与材料完成活动，再追问不清楚的过程。',
         'limits': '只支持研究方法选择，不能用作行业使用现状证据。'},
    ]
    p['interpretation'] = '公开材料支持“值得研究中小团队的知识工作及人机协作”这一方向 [S1][S3]。美国小企业报告提供异地背景 [S2]，不能代替中国创业团队的现状数据。当前真实访谈与问卷样本均为0；以下场景是研究者提出的待验证假设，尚未确认使用频率、采购动机或心理。'
    seeds = [
        ('知识检索与任务交接', '项目负责人 / 新成员', '接手项目，需要确认当前结论与责任人', ['收集文档与消息', 'AI提取候选结论', '核对时间、出处与权限', '向负责人确认后交接'],
         '待问：来源可靠、更新及时、是否接入现有协作工具，哪个因素真正影响选择？',
         '待问：由个人试用还是团队统一采购？文档权限与知识维护由谁负责？',
         '假设：用户可能担心拿到过时结论；需以最近一次错误交接事件及本人表述核对。',
         '资料少、负责人随时可问时，AI检索可能不如直接沟通。', '请2个团队展示一次真实交接；比较原方法与AI方法的核对成本。', ['S1']),
        ('对外内容与方案交付', '运营 / 销售 / 创始人', '要向客户或公众提交材料', ['确认对象与目标', '整理获准使用的业务材料', 'AI起草', '人工核实事实和语气', '审批与发布'],
         '待问：交付质量、事实准确、修改次数、价格和协作便利性如何影响决定？',
         '待问：是否有品牌规范、审批者与客户资料使用约定？',
         '假设：用户可能同时希望提速并保持专业辨识度；不能据此给用户贴心理标签。',
         '信息核实和修改耗时可能抵消起草速度。', '拿3份脱敏交付物，事先约定质量标准，记录准备、生成、修改与审批总耗时。', ['S1', 'S2']),
        ('经营数据解读与汇报', '创始人 / 运营负责人', '需要解释一段时间的经营变化', ['明确指标定义', '导出获准使用的数据', '清洗和计算', 'AI提出解释候选', '回查数字与业务事件', '决定下一步动作'],
         '待问：可复算、可追溯、数据接入和解释可信度是否影响使用？',
         '待问：是否允许上传数据？谁维护指标口径、谁承担错误决策责任？',
         '假设：负责人可能担心“看似合理但无法验证”的解释；需要真实决策事件。',
         '口径混乱时，AI可能放大错误；简单固定报表可能更合适。', '获取一份脱敏表及指标说明，对照人工计算，记录错误与检查成本。', ['S1']),
        ('内部轻量工具与原型', '产品 / 技术 / 创始人', '有一个小任务想通过内部工具完成', ['定义任务与完成标准', 'AI辅助生成原型', '用实际样例试跑', '人工检查错误与数据处理', '选择继续维护或放弃'],
         '待问：试做速度之外，维护成本与实际可用性是否决定继续使用？',
         '待问：谁能发布、谁负责维护、何时用现成产品替代自建？',
         '假设：非技术成员可能期待自主完成，也担心无法定位错误；需区分岗位和经历。',
         '厂商编码对话中的现象不能直接推广到非技术办公人员。', '对照技术与非技术成员各一次真实尝试，记录成功、返工和放弃原因。', ['S3']),
    ]
    for name, role, trigger, workflow, decision, strategy, psychology, counterexample, next_step, refs in seeds:
        p['scenarios'].append(dict(name=name, role=role, trigger=trigger, workflow=workflow, decision=decision, strategy=strategy,
                                   psychology=psychology, counterexample=counterexample, next_step=next_step, evidence_ids=refs,
                                   status='待验证假设', psychology_status='尚无本人表述证据'))
    return p
