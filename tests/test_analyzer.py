from src.analyzer import analyze_local


def test_extracts_actions_and_decisions():
    text = open("data/samples/sample_transcript.txt", encoding="utf-8").read()
    minutes = analyze_local(text)
    assert minutes.summary
    assert minutes.keywords
    assert any("规则兜底" in a.task or "李娜" in a.task for a in minutes.action_items)
    assert any("有效会话" in d or "拍板" in d or "同意" in d for d in minutes.decisions)
    assert minutes.engine.startswith("local")
