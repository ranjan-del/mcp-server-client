"""Tests for the prompt template builders."""

from server.prompts.prompts import build_code_review_prompt, build_summarize_prompt


def test_summarize_prompt_includes_text_and_style():
    prompt = build_summarize_prompt("some content", style="detailed")
    assert "some content" in prompt
    assert "detailed" in prompt


def test_code_review_prompt_wraps_code_in_fence():
    prompt = build_code_review_prompt("print('hi')", language="python")
    assert "print('hi')" in prompt
    assert "```python" in prompt
