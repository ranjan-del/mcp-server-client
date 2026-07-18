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

# Each feature module exposes a `register(mcp)` function that attaches its
# tools/resources/prompts. Importing them here keeps server.py a thin wiring layer.
from server.tools import calculator, database, file_reader, github, notes, weather
from server.resources import resources
from server.prompts import prompts


def build_server() -> FastMCP:
    """Construct and configure the FastMCP server instance.

    Registers every tool, resource and prompt template, then returns the ready
    server. Kept separate from :func:`main` so tests can build the server without
    starting the stdio loop.
    """
    mcp = FastMCP("mcp-server-client")

    # Tools (actions the client can invoke).
    calculator.register(mcp)
    weather.register(mcp)
    file_reader.register(mcp)
    github.register(mcp)
    database.register(mcp)
    notes.register(mcp)

    # Resources (readable data the client can fetch by URI).
    resources.register(mcp)

    # Prompts (reusable, parameterised message templates).
    prompts.register(mcp)

    return mcp


def main() -> None:
    """Build the server and run it over the stdio transport."""
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
