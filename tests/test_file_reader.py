"""Tests for the file_reader tool: reading works, traversal is blocked."""

import pytest

from server.tools.file_reader import FileAccessError, list_files, read_file


@pytest.fixture()
def sandbox(tmp_path):
    """Create a small sandbox with one allowed file and one secret outside it."""
    base = tmp_path / "sandbox"
    base.mkdir()
    (base / "allowed.txt").write_text("safe content", encoding="utf-8")
    (base / "sub").mkdir()
    (base / "sub" / "nested.txt").write_text("nested content", encoding="utf-8")
    # A secret sibling that lives OUTSIDE the sandbox.
    (tmp_path / "secret.txt").write_text("top secret", encoding="utf-8")
    return base


def test_reads_allowed_file(sandbox):
    assert read_file("allowed.txt", base_dir=sandbox) == "safe content"


def test_reads_nested_file(sandbox):
    assert read_file("sub/nested.txt", base_dir=sandbox) == "nested content"


def test_blocks_parent_traversal(sandbox):
    # The classic ../ escape must be refused.
    with pytest.raises(FileAccessError):
        read_file("../secret.txt", base_dir=sandbox)


def test_blocks_absolute_path(sandbox):
    with pytest.raises(FileAccessError):
        read_file("/etc/passwd", base_dir=sandbox)


def test_missing_file_raises(sandbox):
    with pytest.raises(FileAccessError):
        read_file("does_not_exist.txt", base_dir=sandbox)


def test_list_files(sandbox):
    files = list_files(base_dir=sandbox)
    assert "allowed.txt" in files
    assert "sub/nested.txt" in files
    # The out-of-sandbox secret must never be listed.
    assert all("secret" not in f for f in files)
