"""Tests for the streaming / progress-notification path.

Two levels, mirroring tests/test_server.py:

* the pure chunk generator (:func:`iter_file_chunks`) is unit-tested in-process;
* a real stdio round trip asserts the client actually receives
  ``notifications/progress`` messages while ``file_reader`` runs.

MEMORY.md checklist: MCP Client -> streaming.
"""

import asyncio
import sys
from pathlib import Path

import pytest

from server.tools.file_reader import FileAccessError, iter_file_chunks

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def sandbox(tmp_path):
    """A sandbox holding one file whose length is not a multiple of the chunk size."""
    base = tmp_path / "sandbox"
    base.mkdir()
    (base / "chunky.txt").write_text("abcdefghij", encoding="utf-8")  # 10 chars
    (base / "empty.txt").write_text("", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("top secret", encoding="utf-8")
    return base


def test_chunks_reassemble_to_the_whole_file(sandbox):
    chunks = list(iter_file_chunks("chunky.txt", base_dir=sandbox, chunk_size=4))
    assert "".join(c for c, _, _ in chunks) == "abcdefghij"


def test_progress_counts_are_monotonic_and_end_at_the_total(sandbox):
    chunks = list(iter_file_chunks("chunky.txt", base_dir=sandbox, chunk_size=4))
    # 10 chars in chunks of 4 -> 4 + 4 + 2.
    assert [read for _, read, _ in chunks] == [4, 8, 10]
    # The total must be constant and must equal the final running count.
    assert {total for _, _, total in chunks} == {10}


def test_empty_file_still_yields_one_event(sandbox):
    # Consumers should never have to special-case "no progress at all".
    assert list(iter_file_chunks("empty.txt", base_dir=sandbox)) == [("", 0, 0)]


def test_streaming_reader_enforces_the_same_sandbox(sandbox):
    # The generator is lazy, so force it with list() to trigger the check.
    with pytest.raises(FileAccessError):
        list(iter_file_chunks("../secret.txt", base_dir=sandbox))


def test_rejects_non_positive_chunk_size(sandbox):
    with pytest.raises(ValueError):
        list(iter_file_chunks("chunky.txt", base_dir=sandbox, chunk_size=0))


async def _round_trip_with_progress():
    """Call file_reader over stdio and collect the progress notifications."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    seen: list[tuple[float, float | None, str | None]] = []

    async def on_progress(progress, total, message):
        seen.append((progress, total, message))

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "server.server"],
        cwd=str(_REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "file_reader",
                {"relative_path": "sample.txt"},
                progress_callback=on_progress,
            )
    texts = [b.text for b in result.content if getattr(b, "type", None) == "text"]
    return seen, texts


def test_stdio_call_emits_progress_notifications():
    """End-to-end proof that streaming works over the real transport."""
    pytest.importorskip("mcp")
    seen, texts = asyncio.run(_round_trip_with_progress())

    # data/sample.txt is longer than the 32-char default chunk, so more than one
    # notification must have arrived before the single final result.
    assert len(seen) > 1
    progresses = [p for p, _, _ in seen]
    assert progresses == sorted(progresses)
    assert progresses[-1] == seen[-1][1]  # final progress == declared total
    # And the streamed call still returns the complete file contents.
    assert any("Hello from the sandbox." in t for t in texts)
