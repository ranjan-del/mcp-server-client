"""Tests for the github tool: deterministic offline stub."""

import pytest

from server.tools.github import get_repo_info


def test_returns_stub_offline(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    info = get_repo_info("octocat", "hello-world")
    assert info["full_name"] == "octocat/hello-world"
    assert info["source"] == "offline-stub"
    assert info["html_url"] == "https://github.com/octocat/hello-world"
    assert isinstance(info["stars"], int)


def test_deterministic(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert get_repo_info("a", "b") == get_repo_info("a", "b")


def test_requires_owner_and_repo():
    with pytest.raises(ValueError):
        get_repo_info("", "repo")
