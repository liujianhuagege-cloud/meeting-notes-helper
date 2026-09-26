from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer

from .prompts import SYSTEM_PROMPT, user_prompt

load_dotenv()

ACTION_HINTS = (
    "需要",
    "负责",
    "跟进",
    "完成",
    "截止",
    "下周",
    "明天",
    "安排",
    "提交",
    "务必",
    "请",
    "todo",
    "action",
)
DECISION_HINTS = ("决定", "同意", "拍板", "确认采用", "通过", "定为")


@dataclass
class ActionItem:
    task: str
    owner: str = "未知"
    deadline: str = "未知"


@dataclass
class Minutes:
    title: str
    summary: str
    topics: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    engine: str = "local"

    def to_dict(self) -> dict:
        data = asdict(self)
        return data


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？!?\n]+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 6]


def _local_keywords(text: str, top_k: int = 8) -> list[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return []
    vectorizer = TfidfVectorizer(max_features=40, token_pattern=r"(?u)\b\w+\b")
    try:
        matrix = vectorizer.fit_transform(sentences)
    except ValueError:
        return []
    scores = matrix.sum(axis=0).A1
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    stop = {"我们", "你们", "这个", "那个", "一个", "进行", "问题", "可以", "没有"}
    words = [w for w, _ in ranked if w not in stop and not w.isdigit()]
    return words[:top_k]


def _local_summary(text: str, max_sentences: int = 4) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return text[:200]
    if len(sentences) <= max_sentences:
        return "。".join(sentences) + "。"
    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    matrix = vectorizer.fit_transform(sentences)
    scores = matrix.sum(axis=1).A1
    indexed = list(enumerate(scores))
    top = sorted(sorted(indexed, key=lambda x: x[1], reverse=True)[:max_sentences], key=lambda x: x[0])
    return "。".join(sentences[i] for i, _ in top) + "。"


def _guess_owner(sentence: str) -> str:
    m = re.search(r"([\u4e00-\u9fff]{2,4})(负责|跟进|来做|完成)", sentence)
    if m:
        return m.group(1)
    return "未知"


def _guess_deadline(sentence: str) -> str:
    m = re.search(r"(本周|下周|明天|后天|\d{1,2}月\d{1,2}日|周五|周一)", sentence)
    return m.group(1) if m else "未知"


def analyze_local(transcript: str) -> Minutes:
    sentences = _split_sentences(transcript)
    actions = []
    decisions = []
    for s in sentences:
        if any(h in s.lower() for h in ACTION_HINTS):
            actions.append(ActionItem(task=s, owner=_guess_owner(s), deadline=_guess_deadline(s)))
        if any(h in s for h in DECISION_HINTS):
            decisions.append(s)
    keywords = _local_keywords(transcript)
    topics = keywords[:5] or ["综合讨论"]
    first_line = sentences[0][:24] if sentences else "会议纪要"
    return Minutes(
        title=f"{first_line}…",
        summary=_local_summary(transcript),
        topics=topics,
        decisions=decisions[:8],
        action_items=actions[:12],
        keywords=keywords,
        risks=[],
        engine="local-tfidf",
    )


def _parse_llm_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw).removesuffix("```").strip()
    return json.loads(raw)


def analyze_with_llm(transcript: str) -> Minutes:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("未配置 OPENAI_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(transcript)},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    data = _parse_llm_json(content)
    items = [
        ActionItem(
            task=str(x.get("task", "")),
            owner=str(x.get("owner", "未知")),
            deadline=str(x.get("deadline", "未知")),
        )
        for x in data.get("action_items", [])
        if str(x.get("task", "")).strip()
    ]
    return Minutes(
        title=str(data.get("title") or "会议纪要"),
        summary=str(data.get("summary") or ""),
        topics=list(data.get("topics") or []),
        decisions=list(data.get("decisions") or []),
        action_items=items,
        keywords=list(data.get("keywords") or []),
        risks=list(data.get("risks") or []),
        engine=f"llm:{model}",
    )


def analyze(transcript: str, prefer_llm: bool = True) -> Minutes:
    text = transcript.strip()
    if len(text) < 20:
        raise ValueError("转写内容过短，请补充会议文本。")
    if prefer_llm and os.getenv("OPENAI_API_KEY", "").strip():
        try:
            return analyze_with_llm(text)
        except Exception:
            local = analyze_local(text)
            local.engine = "local-tfidf (llm-fallback)"
            return local
    return analyze_local(text)
