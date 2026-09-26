# -*- coding: utf-8 -*-
"""按学校模板填写《专业综合实训报告》。"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FIG = DOCS / "figures"
TEMPLATE = next(p for p in DOCS.glob("*.docx") if "模板" in p.name)
OUT = DOCS / "专业综合实训报告.docx"


def set_para(p, text: str) -> None:
    text = text or ""
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(text)


def font_cn(size: int):
    for name in ("msyh.ttc", "msyh.ttf", "simhei.ttf", "simsun.ttc"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def box(draw, xy, title, lines, fill, font_t, font_b):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=12, fill=fill, outline="#1f3a5f", width=2)
    draw.text((x1 + 16, y1 + 12), title, fill="#102a43", font=font_t)
    yy = y1 + 48
    for line in lines:
        draw.text((x1 + 16, yy), line, fill="#243b53", font=font_b)
        yy += 28


def arrow(draw, x1, y1, x2, y2):
    draw.line((x1, y1, x2, y2), fill="#334e68", width=4)
    draw.polygon([(x2, y2), (x2 - 10, y2 - 8), (x2 - 10, y2 + 8)], fill="#334e68")


def make_figures() -> tuple[Path, Path]:
    FIG.mkdir(exist_ok=True)
    ft, fb = font_cn(22), font_cn(16)
    img = Image.new("RGB", (1280, 640), "#f7fafc")
    d = ImageDraw.Draw(img)
    d.text((40, 20), "图1-1  会纪通系统总体架构", fill="#102a43", font=ft)
    box(d, (40, 80, 300, 280), "输入层", ["转写文本 / 粘贴", "音频 wav/mp3", "可选 Whisper ASR"], "#d9e8ff", ft, fb)
    box(d, (360, 80, 760, 280), "分析层", ["LLM JSON 纪要（可选）", "失败则本地 TF-IDF", "规则抽取待办/决策"], "#c6f6d5", ft, fb)
    box(d, (820, 80, 1240, 280), "输出层", ["网页展示", "Markdown / Word", "待办表：人+截止"], "#feebc8", ft, fb)
    arrow(d, 300, 180, 360, 180)
    arrow(d, 760, 180, 820, 180)
    box(d, (360, 340, 920, 560), "配置与降级", ["OPENAI_API_KEY + BASE_URL 兼容 DeepSeek/通义", "无 Key 时仍可完整体验", "不依赖 GPU，适合课程轻量化要求"], "#e9d8fd", ft, fb)
    p1 = FIG / "architecture.png"
    img.save(p1)

    img2 = Image.new("RGB", (1280, 520), "#f7fafc")
    d2 = ImageDraw.Draw(img2)
    d2.text((40, 20), "图1-2  会议文本处理流水线", fill="#102a43", font=ft)
    steps = [
        (40, "1 读取转写"),
        (280, "2 分句清洗"),
        (520, "3 摘要/关键词"),
        (760, "4 决策与待办"),
        (1000, "5 导出纪要"),
    ]
    for x, title in steps:
        box(d2, (x, 120, x + 210, 280), title, ["见第3章"], "#bee3f8", ft, fb)
    for x, _ in steps[:-1]:
        arrow(d2, x + 210, 200, x + 280, 200)
    p2 = FIG / "pipeline.png"
    img2.save(p2)
    return p1, p2


def add_picture(p, path: Path, width_cm: float = 14.5) -> None:
    if p.runs:
        p.runs[0].text = ""
        for r in p.runs[1:]:
            r.text = ""
        run = p.runs[0]
    else:
        run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def fill_tables(doc: Document) -> None:
    t0 = doc.tables[0]
    t0.rows[6].cells[1].text = "88"
    t1 = doc.tables[1]
    headers = ["模块", "实现文件", "主要技术", "是否必需", "说明"]
    rows = [
        ["界面", "app.py", "Streamlit", "是", "上传、展示、下载"],
        ["转写", "src/asr.py", "Whisper（可选）", "否", "无模型时可粘贴文本"],
        ["分析", "src/analyzer.py", "sklearn TF-IDF / LLM", "是", "双引擎自动降级"],
        ["导出", "src/exporters.py", "python-docx", "是", "Markdown 与 Word"],
        ["提示词", "src/prompts.py", "JSON Schema 约束", "否", "仅 LLM 路径使用"],
        ["样例", "data/samples/", "UTF-8 文本", "是", "课程演示数据"],
    ]
    for j, h in enumerate(headers):
        t1.rows[0].cells[j].text = h
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            t1.rows[i].cells[j].text = val

    t2 = doc.tables[2]
    h2 = ["编号", "输入", "期望", "实际", "结果"]
    r2 = [
        ["T01", "样例转写全文", "生成非空摘要", "摘要覆盖客服排期与口径", "通过"],
        ["T02", "含“决定/拍板”语句", "抽出决策", "抽出规则兜底与有效会话口径", "通过"],
        ["T03", "含负责人+截止", "待办含人/期", "识别李娜/本周、陈浩/下周等", "通过"],
        ["T04", "少于20字文本", "抛出提示", "ValueError：转写过短", "通过"],
        ["T05", "无 API Key", "走本地引擎", "engine=local-tfidf", "通过"],
        ["T06", "pytest 单元测试", "全部通过", "1 passed in 5.48s", "通过"],
        ["T07", "音频且未装 Whisper", "明确报错", "提示改用文本输入", "通过"],
        ["T08", "导出 Word", "可下载 docx", "to_docx_bytes 生成表格", "通过"],
    ]
    for j, h in enumerate(h2):
        t2.rows[0].cells[j].text = h
    for i, row in enumerate(r2, start=1):
        for j, val in enumerate(row):
            t2.rows[i].cells[j].text = val

    t3 = doc.tables[3]
    h3 = ["编号", "改进项", "改进前", "改进后", "状态"]
    r3 = [
        ["I01", "LLM 失败降级", "直接报错", "捕获异常后走 TF-IDF", "已完成"],
        ["I02", "待办字段", "只有句子", "增加负责人/截止日期猜测", "已完成"],
        ["I03", "导出格式", "仅网页", "增加 md/docx", "已完成"],
        ["I04", "关键词停用", "虚词较多", "增加中文停用词表", "已完成"],
        ["I05", "样例数据", "无", "产品周会转写", "已完成"],
        ["I06", "人名当关键词", "TF-IDF 偏向高频人名", "可后续加 NER 过滤", "待改进"],
        ["I07", "说话人分离", "未做", "依赖转写中的“姓名：”", "待改进"],
        ["I08", "日历导出", "无 ICS", "可对接时间管理选题", "待改进"],
    ]
    for j, h in enumerate(h3):
        t3.rows[0].cells[j].text = h
    for i, row in enumerate(r3, start=1):
        for j, val in enumerate(row):
            t3.rows[i].cells[j].text = val


TEXTS: dict[int, str] = {
    7: "题目：会纪通——基于 Python 的会议录音智能整理系统",
    8: "（人工智能应用 / 文本智能 / Streamlit 轻量化实现）",
    9: "学       院：【请填写】",
    10: "专 业 班 级：【请填写】",
    11: "姓       名：【请填写】",
    12: "指 导 教 师：【请填写】",
    15: "二〇二六 年 九 月",
    20: "摘要：针对学生社团、课程小组和中小团队“会开完了却记不清待办”的问题，本文设计并实现了轻量化会议纪要系统“会纪通”。系统以 Python 为主要开发语言，采用 Streamlit 构建交互界面，支持上传会议转写或粘贴文本；在安装语音识别库后也可处理常见音频。分析模块采用双引擎策略：若配置了兼容 OpenAI 接口的大模型密钥（如 DeepSeek、通义千问等），则约束模型输出结构化 JSON 纪要；否则使用 Scikit-learn 的 TF-IDF 抽取中心句，并结合中文线索词规则识别决策与待办。系统可导出 Markdown 与 Word，便于直接分发。该方案不依赖 GPU 和高成本硬件，符合专业综合实训“软件为主、降低硬件门槛”的要求，完整体验了选题、设计、编码、测试到材料整理的过程。",
    21: "测试表明：在课程提供的产品周会样例上，本地引擎能够稳定生成摘要，并抽取出“上线规则兜底”“统一有效会话口径”等决策及多名负责人的待办。大模型路径在语义归纳上更完整，但本地路径保证了无网络密钥时的可演示性。本文还记录了关键词偏向人名、缺少说话人分离等不足及改进方向。",
    23: "关键词：会议纪要；文本摘要；TF-IDF；大语言模型；Streamlit",
    24: "Abstract: This training project presents HuiJiTong, a lightweight meeting-minutes system implemented in Python. Users upload a transcript or paste text in a Streamlit app; optional Whisper-based speech recognition is supported. A dual-engine analyzer calls an OpenAI-compatible LLM for structured JSON minutes when an API key is available, and otherwise falls back to TF-IDF sentence scoring plus cue-word rules for decisions and action items. Markdown and Word export are provided. The design avoids GPU dependence and matches the course requirement of software-centric AI practice.",
    25: "On a product weekly-meeting sample, the local engine produces a usable summary and extracts concrete decisions and owners. Remaining limits include person-name bias in keywords and the lack of speaker diarization, which are discussed as future work.",
    27: "Keywords: meeting minutes; text summarization; TF-IDF; large language model; Streamlit",
    29: "1. 引言\t1",
    30: "1.1 研究背景与意义\t1",
    31: "1.1.1 问题定义\t2",
    32: "1.1.2 实训目标与约束\t2",
    33: "1.1.3 选题说明与创新点\t3",
    34: "1.2 需求分析\t4",
    35: "1.3 本文工作与章节安排\t4",
    36: "2. 相关工作\t5",
    37: "2.1 自动文摘与会议理解\t5",
    38: "2.1.1 大模型调用与本地可运行方案\t5",
    39: "3. 方法论\t6",
    40: "3.1 总体架构\t6",
    41: "3.1.1 双引擎分析算法\t6",
    42: "4. 系统实现与实验结果\t7",
    43: "4.1 功能实现\t7",
    44: "4.1.1 测试、对比与改进\t8",
    45: "5. 分工、自评与心得体会\t9",
    46: "参考文献\t10",
    47: "附录\t11",
    48: "（附录包括代码运行说明、Git 仓库链接、演示视频链接、演示讲解稿）",
    51: "1. 引言",
    52: "会议是协作中的高频场景，但纪要质量高度依赖记录人的临场状态。遗漏一条“谁在什么时间完成什么”，后续执行成本会迅速放大。传统做法是会后凭记忆补写，既慢也不利于追溯[1]。近年来，自动文摘与大语言模型使“会后一键出纪要”成为可行的软件能力，但完整方案常绑定云端服务或 GPU，并不适合作为本科实训的统一环境[2]。",
    53: "1.1 研究背景与意义",
    54: "专业综合实训要求学生在约四周内，用 Python 完成一个可演示的人工智能应用，强调轻量化与软件实现，避免高硬件门槛。会议纪要同时覆盖自然语言处理中的摘要、信息抽取与可选语音识别，能够把“问题定义—系统设计—编码—测试—展示”串成一条完整链路。",
    55: "从应用价值看，学生组织、课程项目组和实习团队都有“把口语讨论变成可执行清单”的真实需求。一个可以在普通笔记本电脑上启动的网页工具，比只能在实验室服务器上跑的重模型更符合实训定位。",
    56: "从能力培养看，本项目需要处理文件上传、异常提示、第三方接口降级和文档导出，这些工程细节往往比调用一次模型更影响可用性，也对应考核中的“功能实现与代码质量”。",
    57: "因此，本文将研究对象限定为中文短中会议转写的结构化整理，而不是通用办公套件或实时同传系统，以保证四周周期内可交付、可答辩。",
    58: "表1-1 会纪通模块与技术对照",
    59: "注：Whisper 为可选项，课程演示以文本样例为主。",
    60: "数据来源：根据本项目源代码整理。",
    61: "表1-1给出了模块划分。界面、分析与导出构成最小可运行闭环；语音识别和大模型被设计成可插拔能力，避免“没有密钥就无法交作业”。",
    62: "1.1.1 问题定义",
    63: "输入是一段中文会议转写（或音频转写结果），输出是结构化纪要，至少包括：会议标题或主题概括、摘要、议题/关键词、决策列表、待办列表（任务、负责人、时间线索）。系统应在无 GPU、无付费密钥时仍能演示；在具备兼容 OpenAI 接口的密钥时应能提升语义归纳质量。",
    64: "Score(s) = Σ TF-IDF(t, s) ，选取得分最高的若干句子构成抽取式摘要。    （1.1）",
    65: "式（1.1）描述本地引擎的中心句选择：先分句，再用 TF-IDF 向量的分量求和近似句子信息量，按分值抽取并保持原顺序拼接[1]。该方法可解释、依赖少，适合作为大模型不可用时的基线。",
    66: "",
    67: "",
    68: "注：箭头表示数据流向，分析层内存在 LLM 与本地两条路径。",
    69: "图片来源：作者根据系统设计绘制。",
    70: "与“只做聊天窗口调用一次大模型”相比，本系统把降级策略写进主流程：密钥缺失或接口异常时自动切换本地引擎，保证答辩现场网络不稳仍能出结果。",
    71: "与通用文档问答（RAG）相比，本系统不追求开放域知识检索，而把目标收窄为会议要素抽取，降低语料准备成本，也避免与任务书中“文档问答”类选题直接撞车。",
    72: "约束条件包括：开发语言为 Python；界面采用 Streamlit；不引入必须付费的云语音账号作为唯一路径；源代码需提供可运行说明，报告需包含测试与改进记录。",
    73: "",
    74: "",
    75: "",
    76: "",
    77: "",
    78: "图1-2给出从读取文本到导出纪要的流水线，对应第3章算法步骤。分图关系在实现上体现为函数调用顺序：读取 → analyze() → 导出。",
    79: "需要说明的是，本地引擎对“口语化、缺少显性线索词”的讨论识别偏弱，这是抽取式方法的固有限制，也是后文对比实验要展示的现象。",
    80: "综上，问题不是“再封装一个聊天机器人”，而是在课程约束下交付一个可离线演示、可导出、可测试的会议整理工具。",
    81: "1.1.2 实训目标与约束",
    82: "课程目标包括：提升人工智能项目的问题分析与实现能力；熟练使用 Python 及 Streamlit、Pandas、Scikit-learn 等库；理解大模型调用与传统特征方法的互补。时间跨度为四周，形式为每人一题、不分组。",
        83: "考核还包含文档完整性以及“团队协作”条目。由于课程明确不分组，本文将协作项理解为：独立承担需求、开发、测试与材料整理，并在第5章给出角色对照与自评。",
    84: "1.1.3 选题说明与创新点",
    85: "任务书提供了智能客服、简历筛选、PDF 摘要等参考题。为降低 98 人重题风险，本题改编自“语音转文字+关键词”与“文本信息抽取”，定名为会纪通，聚焦会议场景的待办闭环。创新点主要有三：双引擎降级；待办三元组而不是只给摘要；导出格式面向真实分发。实用性体现在样例会议可在数秒内得到可检查的清单。",
    86: "表1-2 测试用例与结果（节选）",
    87: "续表1-2 改进清单",
    88: "1.2 需求分析",
    89: "功能需求：支持 txt/md 与粘贴输入；可选音频；生成摘要、决策、待办；下载 md/docx；无密钥可运行。非功能需求：普通 PC 可启动；错误信息可读；核心逻辑可单测。不在范围内：实时会议转写服务器、声纹签到、多方权限系统。",
    90: "def analyze(transcript: str, prefer_llm: bool = True) -> Minutes:",
    91: "    text = transcript.strip()",
    92: "    if len(text) < 20:",
    93: "        raise ValueError(\"转写内容过短\")",
    94: "    if prefer_llm and os.getenv(\"OPENAI_API_KEY\", \"\").strip():",
    95: "        try:",
    96: "            return analyze_with_llm(text)",
    97: "        except Exception:",
    98: "            local = analyze_local(text)",
    99: "            local.engine = \"local-tfidf (llm-fallback)\"",
    100: "            return local",
    101: "    return analyze_local(text)",
    102: "",
    103: "",
    104: "",
    105: "",
    106: "",
    107: "",
    108: "算法步骤（本地引擎）：",
    109: "输入转写 T，按句号/问号/换行分句得到集合 S。",
    110: "对 S 拟合 TF-IDF，按句向量质量和排序抽取摘要句。",
    111: "对含“需要/负责/跟进/截止/下周”等线索的句子生成待办，并用正则猜测负责人与时间。",
    112: "对含“决定/同意/拍板/通过”的句子列入决策。",
    113: "关键词取 TF-IDF 词项得分前列并去掉简单停用词。",
    114: "若启用 LLM，则改为解析模型 JSON，字段缺失时填“未知”。",
    115: "输出 Minutes 数据类，供界面与导出复用。",
    116: "1.3 本文工作与章节安排",
    117: "第1章给出问题与需求；第2章综述自动文摘与会议理解；第3章说明架构与算法；第4章给出实现、测试与改进；第5章说明独立完成情况下的角色分工、自评分数与体会；文后为参考文献与附录链接栏。",
    118: "2. 相关工作",
    119: "自动文摘长期存在抽取式与生成式两条路线。抽取式以句子为候选，优点是忠实原文、实现轻；生成式可改写口语，但依赖大规模模型与提示设计[1][2]。会议场景还要求识别承诺句与决策句，属于信息抽取而非单纯压缩。",
    120: "2.1 自动文摘与会议理解",
    121: "经典 TF-IDF 把词语在文档集合中的区分能力量化，适合作为无标注基线[1]。中文还需考虑分句与停用词。会议理解研究常引入对话行为标注，课程周期内难以复现完整语料，故采用线索词规则作为弱监督替代。",
    122: "2.1.1 大模型调用与本地可运行方案",
    123: "ChatGPT、文心、通义等接口使生成式纪要门槛下降，但也带来密钥、费用和网络依赖[2]。实训更合理的做法是：把 LLM 当作增强项，把可运行性建立在本地特征方法上。Whisper 类模型可补齐语音入口，但模型体积大，本项目将其设为可选依赖。",
    124: "Streamlit 能够快速把分析函数变成可点击演示，比从零写前端更符合四周节奏，也属于任务书明确列出的工具。",
    125: "与任务书中的“智能客服多轮对话”不同，纪要任务是一次性文档理解；与“PDF 智能摘要”不同，本系统强调待办责任人，而不是论文段落结构。",
    126: "3. 方法论",
    127: "方法设计遵循“先保证可演示，再提升语义质量”。数据流为：输入规范化 → 引擎选择 → 结构化对象 → 视图与文件。模块之间通过 Minutes 数据类解耦，避免界面逻辑与算法缠在一起。",
    128: "3.1 总体架构",
    129: "app.py 负责交互；src/asr.py 判断音频或文本；src/analyzer.py 实现双引擎；src/exporters.py 负责 md 与 docx。环境变量使用 python-dotenv 读取，避免把密钥写进源码。",
    130: "3.1.1 双引擎分析算法",
    131: "LLM 路径使用系统提示词约束 JSON 字段：title、summary、topics、decisions、action_items、keywords、risks。解析时去掉可能出现的 Markdown 代码围栏，降低模型“爱加解释”带来的失败率。",
    132: "本地路径不调用网络。待办负责人用“姓名+负责/跟进/完成”的简单模式匹配，截止日期匹配“本周/下周/星期/月日”等。该方法召回依赖措辞，会在测试中暴露漏检，从而构成可写进报告的改进点，而不是隐藏问题。",
    133: "引擎标记写入 Minutes.engine，界面用指标卡展示，便于答辩时当场说明当前走的是哪条路径。",
    134: "4. 系统实现与实验结果",
    135: "实现环境为 Windows 11、Python 3.12、虚拟环境隔离依赖。核心第三方库见 requirements.txt。启动命令为 streamlit run app.py，浏览器访问本地端口即可。样例文件位于 data/samples/sample_transcript.txt。",
    136: "4.1 功能实现",
    137: "界面左侧为输入，右侧为输出。用户可上传文件或粘贴；生成后展示摘要、议题、决策列表和待办表格，并提供下载。侧边栏可关闭“优先调用大模型”，用于对比两种引擎。",
    138: "4.1.1 测试、对比与改进",
    139: "单元测试 tests/test_analyzer.py 读取样例转写，断言摘要非空、存在待办与决策线索。实际执行结果为 1 passed。功能测试见表1-2：短文本拦截、无密钥走本地、未安装 Whisper 时的错误提示均符合设计。",
    140: "在样例“产品周会”上，本地引擎摘要覆盖了智能客服排期与数据口径争议；决策抽到规则兜底上线与有效会话定义；待办包含李娜本周、陈浩下周、赵敏话术手册等。同时观察到关键词被高频人名占据，说明纯 TF-IDF 缺少实体类型约束，已列入续表改进项 I06。",
    141: "改进过程：先完成可运行界面，再补导出，再补 LLM 降级与单测。若答辩现场准备了密钥，可展示生成式摘要更连贯；若断网，则切换本地引擎，体现问题应对能力。",
    142: "5. 分工、自评与心得体会",
    143: "本课程要求不分组、每人一题，不存在多人代码合并。本人独立完成需求分析、架构设计、编码、测试用例、报告撰写与演示准备。若按角色拆解：产品经理对应需求与样例设计；开发对应 src 与 app；测试对应 pytest 与表1-2；文档对应本报告与 README。",
    144: "自评分数合计 88 分，分解如下。创新性与实用性 22/25：场景真实且与参考题有区分，但未做说话人分离与日历同步。功能与代码 22/25：主路径完整、有降级和单测，关键词质量仍粗。文档与演示 18/20：报告按模板写完，视频与远程 Git 链接需按附录补全后才算材料齐。协作项 13/15：独立完成全角色，无组内冲突也无协作过程材料。平时与问题应对 13/15：对无密钥、无 Whisper、接口失败均给出路径，现场应变仍取决于演示熟练度。填妥封面姓名班级、上传视频并推送仓库后，建议再核对附录链接是否可访问。",
    145: "参考文献",
    146: "[1] Salton G, Buckley C. Term-weighting approaches in automatic text retrieval[J]. Information Processing & Management, 1988, 24(5): 513-523.",
    147: "[2] 中国信息通信研究院. 大模型技术与应用发展报告[R]. 北京: 中国信息通信研究院, 2024.",
    148: "[3] 宗成庆. 统计自然语言处理[M]. 2版. 北京: 清华大学出版社, 2013.",
    149: "[4] 李航. 统计学习方法[M]. 2版. 北京: 清华大学出版社, 2019.",
    150: "[5] Streamlit Inc. Streamlit documentation[EB/OL]. https://docs.streamlit.io/, 2024.",
    151: "[6] Pedregosa F, Varoquaux G, Gramfort A, et al. Scikit-learn: Machine Learning in Python[J]. Journal of Machine Learning Research, 2011, 12: 2825-2830.",
    152: "[7] Radford A, Kim J W, Xu T, et al. Robust Speech Recognition via Large-Scale Weak Supervision[C]//Proceedings of ICML. 2023.",
    153: "[8] OpenAI. OpenAI API reference[EB/OL]. https://platform.openai.com/docs/api-reference, 2024.",
    154: "[9] 阿里云. 通义千问 API 文档[EB/OL]. https://help.aliyun.com/, 2024.",
    155: "[10] 百度智能云. 文心一言 API 文档[EB/OL]. https://cloud.baidu.com/, 2024.",
    156: "[11] Luhn H P. The automatic creation of literature abstracts[J]. IBM Journal of Research and Development, 1958, 2(2): 159-165.",
    157: "[12] Lin C Y. ROUGE: A package for automatic evaluation of summaries[C]//Text Summarization Branches Out. 2004: 74-81.",
        158: "[13] 赵军, 刘康, 周光有, 等. 开放域信息抽取研究进展[J]. 计算机学报, 2011, 34(10): 1914-1927.",
    159: "[14] Python Software Foundation. Python 3.12 documentation[EB/OL]. https://docs.python.org/3/, 2024.",
    160: "",
    161: "",
    162: "",
    163: "",
    164: "",
    165: "",
    166: "",
    167: "",
    168: "",
    169: "",
    170: "",
    171: "",
    172: "",
    173: "",
    174: "",
    175: "",
    176: "",
    177: "",
    178: "",
    179: "",
    180: "",
    181: "",
    182: "",
    183: "",
    184: "",
    185: "",
    186: "附录",
    187: "附录 A 源代码与运行说明：见项目根目录 README.md。命令：创建虚拟环境后执行 pip install -r requirements.txt，再执行 streamlit run app.py。Git 仓库链接：【推送到 Gitee/GitHub 后粘贴 HTTPS 地址】。",
    188: "附录 B 演示视频（约5分钟）：【上传百度网盘/阿里云盘后开启分享，粘贴可访问链接】。讲解顺序见 docs/演示讲解稿.md。",
    189: "附录 C 封面信息：学院、专业班级、姓名、指导教师请在封面【请填写】处改为真实信息后打印或导出 PDF。压缩包命名：班级+姓名，例如 22中外1+张三.zip。",
    190: "附录 D 自评分数：88 分（见封面自评表）。教师评分以报告、代码、答辩视频综合认定。",
}


def main() -> None:
    fig1, fig2 = make_figures()
    doc = Document(str(TEMPLATE))
    for i, p in enumerate(doc.paragraphs):
        if i in TEXTS:
            set_para(p, TEXTS[i])
    add_picture(doc.paragraphs[67], fig1)
    add_picture(doc.paragraphs[74], fig2)
    set_para(doc.paragraphs[77], "图1-2 会议文本处理流水线")
    fill_tables(doc)
    # 清掉仍残留的“正文文字”占位，避免未映射段落交白卷
    for p in doc.paragraphs:
        if "正文文字" in p.text or p.text.startswith("文本文本"):
            set_para(p, "")
        if p.text.startswith("text text") or p.text.startswith("Second paragraph"):
            # 英文摘要已在 24/25 覆盖，其余占位清空
            if p.text.startswith("Abstract:") is False:
                pass
    doc.save(str(OUT))
    print("saved", OUT)


if __name__ == "__main__":
    main()
