# 会纪通 · 会议录音智能整理

Python + Streamlit 的轻量 AI 实训项目：把会议录音或转写整理成摘要、议题、决策和待办。

**无大模型 Key 也能跑**（本地 TF-IDF 抽取）。配置 DeepSeek / 通义 / OpenAI 兼容接口后，纪要质量明显更好。

## 环境

- Python 3.10+（推荐 3.11）
- Windows / macOS / Linux

语音识别为可选项：`pip install openai-whisper`（首次会下载模型，体积较大）。课程演示用仓库内样本转写即可。

## 安装与运行

```bash
cd meeting-minutes-ai
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

浏览器打开终端提示的本地地址（一般为 http://localhost:8501）。

1. 点击上传，选择 `data/samples/sample_transcript.txt`
2. 点击「生成纪要」
3. 下载 Markdown 或 Word

## 可选：大模型

编辑 `.env`：

```
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

通义兼容示例：`OPENAI_BASE_URL` 填百炼/灵积文档中的 OpenAI 兼容地址，`OPENAI_MODEL` 填 `qwen-turbo`。

## 可选：音频转写

```bash
pip install openai-whisper
```

上传 wav/mp3。未安装时请粘贴转写文本。

## 项目结构

```
app.py                 Streamlit 入口
src/asr.py             音频/文本读取
src/analyzer.py        本地抽取 + LLM 纪要
src/exporters.py       Markdown / Word 导出
src/prompts.py         大模型提示词
data/samples/          演示转写
tests/                 单元测试
docs/实训报告草稿.md   报告可改写成 Word
```

## 测试

```bash
pytest -q
```

## 提交说明

实训要求源码以 git 仓库链接放入报告附件。本机若未安装 Git：

1. 安装 https://git-scm.com/download/win
2. `git init` → `git add .` → `git commit -m "init meeting minutes ai"`
3. 推送到 GitHub / Gitee，把 HTTPS 链接写进报告

演示视频：录制 Streamlit 操作约 5 分钟，上传网盘，链接写入报告附件。

打包命名按任务书：`班级+姓名`，例如 `22中外1+张三.zip`。
