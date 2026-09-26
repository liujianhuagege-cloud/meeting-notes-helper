from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import streamlit as st

from src.analyzer import analyze
from src.asr import is_audio, read_transcript_file, transcribe_audio
from src.exporters import to_docx_bytes, to_markdown

st.set_page_config(page_title="会纪通 · 会议录音智能整理", page_icon="📝", layout="wide")

st.title("会纪通 · 会议录音智能整理")
st.caption("上传录音或转写文本，自动生成摘要、议题、决策与待办清单。无 API Key 时使用本地 TF-IDF 抽取。")

with st.sidebar:
    st.header("使用说明")
    st.markdown(
        """
1. 上传 `.txt` 转写，或 `.wav/.mp3` 录音  
2. 可选配置 `.env` 中的大模型 Key，效果更好  
3. 点击「生成纪要」，下载 Markdown / Word
        """
    )
    prefer_llm = st.toggle("优先调用大模型", value=True)
    st.markdown("[配置示例](.env.example) 支持 DeepSeek / 通义 / OpenAI 兼容接口")

col_in, col_out = st.columns([1, 1])

with col_in:
    st.subheader("输入")
    uploaded = st.file_uploader(
        "上传音频或转写",
        type=["txt", "md", "wav", "mp3", "m4a", "ogg", "flac"],
    )
    pasted = st.text_area("或直接粘贴会议转写", height=280, placeholder="张三：下周一下午把原型交给李四……")

transcript = ""
asr_note = ""

if pasted.strip():
    transcript = pasted.strip()
elif uploaded is not None:
    suffix = Path(uploaded.name).suffix.lower()
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name
    try:
        if is_audio(tmp_path):
            with st.spinner("正在语音识别，首次加载模型较慢…"):
                transcript = transcribe_audio(tmp_path)
            asr_note = "来源：音频转写"
        else:
            transcript = read_transcript_file(tmp_path)
            asr_note = "来源：文本文件"
    except Exception as exc:
        st.error(str(exc))

if asr_note:
    st.info(asr_note)

run = st.button("生成纪要", type="primary", disabled=not bool(transcript))

if run:
    try:
        minutes = analyze(transcript, prefer_llm=prefer_llm)
        st.session_state["minutes"] = minutes
        st.session_state["transcript"] = transcript
    except Exception as exc:
        st.error(str(exc))

minutes = st.session_state.get("minutes")

with col_out:
    st.subheader("输出")
    if not minutes:
        st.empty()
        st.write("生成后将在这里展示摘要与待办。")
    else:
        st.metric("引擎", minutes.engine)
        st.markdown(f"### {minutes.title}")
        st.write(minutes.summary)
        st.markdown("**议题**")
        st.write("、".join(minutes.topics) or "（无）")
        st.markdown("**决策**")
        for d in minutes.decisions or ["（无）"]:
            st.write(f"- {d}")
        st.markdown("**待办**")
        if minutes.action_items:
            df = pd.DataFrame([a.__dict__ for a in minutes.action_items])
            df.columns = ["任务", "负责人", "截止"]
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.write("未识别到明确待办。")
        st.markdown("**关键词**：" + ("、".join(minutes.keywords) or "无"))
        if minutes.risks:
            st.warning("风险/待确认：" + "；".join(minutes.risks))

        md = to_markdown(minutes, st.session_state.get("transcript"))
        docx = to_docx_bytes(minutes)
        c1, c2 = st.columns(2)
        c1.download_button("下载 Markdown", md.encode("utf-8"), file_name="minutes.md", mime="text/markdown")
        c2.download_button(
            "下载 Word",
            docx,
            file_name="minutes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

with st.expander("原始转写"):
    st.text(st.session_state.get("transcript") or transcript or "暂无")
