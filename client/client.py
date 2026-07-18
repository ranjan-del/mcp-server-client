"""MCP client.

MEMORY.md checklist: connect, list tools, call tools, read resources, streaming.

This client launches ``server/server.py`` as a subprocess and talks to it over
the stdio transport using the official ``mcp`` SDK. It walks through the full
discovery/invocation lifecycle so you can see MCP end-to-end:

  1. connect + initialize a session
  2. list the tools the server advertises
  3. call a tool (the calculator)
  4. list + read a resource
  5. list + render a prompt template
  6. demonstrate progress/streaming handling

If the ``mcp`` SDK is not importable for some reason, ``main`` falls back to a
"direct" demo that exercises the tool modules in-process, so the file always runs
and always shows the logic working.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Make the repo root importable so the fallback demo can import server.tools.*
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


async def run_stdio_demo() -> None:
    """Connect to the server over stdio and exercise the MCP lifecycle."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Launch `python -m server.server` as a subprocess; we speak MCP over its
    # stdin/stdout. cwd is the repo root so the `server` package imports cleanly.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "server.server"],
        cwd=str(_REPO_ROOT),
    )

    print("== Connecting to MCP server over stdio ==")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize -- the MCP handshake exchanging capabilities.
            await session.initialize()
            print("Connected and initialized.\n")

            # 2. List tools.
            tools = await session.list_tools()
            print("== Tools advertised by the server ==")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description or ''}".rstrip())
            print()

            # 3. Call a tool: the calculator.
            print("== Calling tool: calculator('2 + 3 * 4') ==")
            result = await session.call_tool("calculator", {"expression": "2 + 3 * 4"})
            for block in result.content:
                if getattr(block, "type", None) == "text":
                    print(f"  -> {block.text}")
            print()

            # Call another tool with structured output: notes CRUD.
            print("== Calling tool: notes_create('buy milk') ==")
            created = await session.call_tool("notes_create", {"text": "buy milk"})
            print(f"  -> {created.structuredContent or created.content}")
            print()

            # 4. List + read a resource.
            resources = await session.list_resources()
            print("== Resources advertised by the server ==")
            for res in resources.resources:
                print(f"  - {res.uri}: {res.name}")
            print()

            print("== Reading resource: config://server ==")
            config = await session.read_resource("config://server")
            for content in config.contents:
                text = getattr(content, "text", "")
                # Print just the first few lines to keep output tidy.
                preview = "\n".join(text.splitlines()[:8])
                print(preview)
            print()

            # 5. List + render a prompt template.
            prompts = await session.list_prompts()
            print("== Prompts advertised by the server ==")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description or ''}".rstrip())
            print()

            print("== Rendering prompt: summarize ==")
            rendered = await session.get_prompt(
                "summarize", {"text": "MCP lets servers expose tools to LLMs."}
            )
            for message in rendered.messages:
                content = message.content
                text = getattr(content, "text", str(content))
                print(f"  [{message.role}] {text}")
            print()

            # 6. Streaming / progress. The MCP protocol streams *progress
            #    notifications* during a long call rather than partial token text.
            #    Our reference tools return complete results in one shot, so there
            #    is nothing to stream here; we simply note how it would be wired.
            print("== Streaming ==")
            print("  Reference tools return complete results, so no incremental")
            print("  chunks are emitted. For a long-running tool the server would")
            print("  call ctx.report_progress(...) and the client would receive")
            print("  progress notifications via a progress callback.")

    print("\n== Demo complete ==")


def run_direct_demo() -> None:
    """Fallback: exercise the tool modules in-process (no MCP transport)."""
    from server.tools.calculator import calculate
    from server.tools.notes import NotesStore
    from server.tools.weather import get_weather

    print("== Direct (in-process) demo -- MCP SDK unavailable ==")
    print(f"calculate('2 + 3 * 4') -> {calculate('2 + 3 * 4')}")

    store = NotesStore()
    note_id = store.create("buy milk")
    print(f"notes.create('buy milk') -> id {note_id}; list -> {store.list()}")

    print(f"get_weather('London') -> {get_weather('London')}")


def main() -> None:
    """Entry point: run the stdio demo, falling back to the direct demo."""
    try:
        import mcp  # noqa: F401 - just probing availability
    except ImportError:
        run_direct_demo()
        return

    asyncio.run(run_stdio_demo())


if __name__ == "__main__":
    main()
