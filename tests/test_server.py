"""Server tests.

Two levels:

* ``test_build_server_registers_everything`` builds the FastMCP server in-process
  and asserts that all expected tools/resources/prompts were registered.
* ``test_stdio_round_trip`` launches the server as a real subprocess and does a
  full MCP handshake + tool call over stdio -- the end-to-end smoke test.
"""

import asyncio
import sys
from pathlib import Path

import pytest

from server.server import build_server

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_server_registers_everything():
    mcp = build_server()

    # list_tools / list_resources / list_prompts are async; drive them directly.
    tools = asyncio.run(mcp.list_tools())
    tool_names = {t.name for t in tools}
    # Every tool family from MEMORY.md must be present.
    assert {"calculator", "weather", "file_reader", "github",
            "db_insert", "db_query", "notes_create"} <= tool_names

    prompts = asyncio.run(mcp.list_prompts())
    prompt_names = {p.name for p in prompts}
    assert {"summarize", "code_review"} <= prompt_names

    resources = asyncio.run(mcp.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert "config://server" in resource_uris


async def _round_trip():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "server.server"],
        cwd=str(_REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert "calculator" in names

            result = await session.call_tool("calculator", {"expression": "6 * 7"})
            texts = [b.text for b in result.content if getattr(b, "type", None) == "text"]
            assert any("42" in t for t in texts)
            return names


def test_stdio_round_trip():
    """Full client<->server round trip over stdio (skips if SDK missing)."""
    pytest.importorskip("mcp")
    names = asyncio.run(_round_trip())
    assert "notes_create" in names
