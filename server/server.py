"""MCP server entrypoint.

Wires the tools, resources and prompt templates described in MEMORY.md into a
single FastMCP server and serves them over the stdio transport.

FastMCP (from the official ``mcp`` SDK) is a high-level helper: you decorate a
plain Python function with ``@mcp.tool()`` / ``@mcp.resource(...)`` /
``@mcp.prompt()`` and it handles the JSON-RPC wiring, schema generation from type
hints, and the protocol handshake for you.

Run it directly for a stdio server::

    python -m server.server

The accompanying client (``client/client.py``) launches this module as a
subprocess and talks to it over stdio.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# Each feature package exposes a `register_all(mcp)` helper that attaches its
# tools/resources/prompts. Delegating to them keeps server.py a thin wiring layer.
from server.tools import register_all as register_tools
from server.resources import register_all as register_resources
from server.prompts import register_all as register_prompts


def build_server() -> FastMCP:
    """Construct and configure the FastMCP server instance.

    Registers every tool, resource and prompt template, then returns the ready
    server. Kept separate from :func:`main` so tests can build the server without
    starting the stdio loop.
    """
    mcp = FastMCP("mcp-server-client")

    # Tools (actions the client can invoke).
    register_tools(mcp)

    # Resources (readable data the client can fetch by URI).
    register_resources(mcp)

    # Prompts (reusable, parameterised message templates).
    register_prompts(mcp)

    return mcp


def main() -> None:
    """Build the server and run it over the stdio transport."""
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
