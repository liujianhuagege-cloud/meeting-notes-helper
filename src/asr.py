from __future__ import annotations

from pathlib import Path


SUPPORTED_AUDIO = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}


def is_audio(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_AUDIO


def transcribe_audio(file_path: str | Path) -> str:
    """优先使用本地 openai-whisper；未安装时给出明确提示。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"音频不存在: {path}")

    try:
        import whisper  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "未安装语音识别依赖。请执行 pip install openai-whisper，"
            "或直接上传/粘贴会议转写文本。"
        ) from exc

    model = whisper.load_model("base")
    result = model.transcribe(str(path), language="zh")
    text = (result.get("text") or "").strip()
    if not text:
        raise RuntimeError("语音识别结果为空，请检查音频是否清晰。")
    return text


def read_transcript_file(file_path: str | Path) -> str:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        raise ValueError("转写文件为空。")
    return text
