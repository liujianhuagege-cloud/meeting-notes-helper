from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document

from .analyzer import Minutes


def to_markdown(minutes: Minutes, transcript: str | None = None) -> str:
    topics_block = [f"- {t}" for t in minutes.topics] or ["- （无）"]
    decisions_block = [f"- {d}" for d in minutes.decisions] or ["- （无）"]
    risks_block = [f"- {r}" for r in minutes.risks] or ["- （无）"]
    lines = [
        f"# {minutes.title}",
        "",
        f"> 生成引擎：{minutes.engine}",
        "",
        "## 摘要",
        minutes.summary,
        "",
        "## 议题",
        *topics_block,
        "",
        "## 决策",
        *decisions_block,
        "",
        "## 待办",
    ]
    if minutes.action_items:
        for item in minutes.action_items:
            lines.append(f"- [{item.owner} / {item.deadline}] {item.task}")
    else:
        lines.append("- （无）")
    lines += [
        "",
        "## 关键词",
        ", ".join(minutes.keywords) or "（无）",
        "",
        "## 风险与待确认",
        *risks_block,
    ]
    if transcript:
        lines += ["", "## 原始转写", transcript]
    return "\n".join(lines) + "\n"


def to_docx_bytes(minutes: Minutes) -> bytes:
    doc = Document()
    doc.add_heading(minutes.title, level=0)
    doc.add_paragraph(f"生成引擎：{minutes.engine}")
    doc.add_heading("摘要", level=1)
    doc.add_paragraph(minutes.summary)
    doc.add_heading("议题", level=1)
    for t in minutes.topics:
        doc.add_paragraph(t, style="List Bullet")
    doc.add_heading("决策", level=1)
    for d in minutes.decisions or ["（无）"]:
        doc.add_paragraph(d, style="List Bullet")
    doc.add_heading("待办", level=1)
    table = doc.add_table(rows=1, cols=3)
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "任务", "负责人", "截止"
    for item in minutes.action_items:
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text = item.task, item.owner, item.deadline
    doc.add_heading("关键词", level=1)
    doc.add_paragraph("、".join(minutes.keywords))
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def save_markdown(minutes: Minutes, path: str | Path, transcript: str | None = None) -> None:
    Path(path).write_text(to_markdown(minutes, transcript), encoding="utf-8")
