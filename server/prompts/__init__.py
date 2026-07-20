"""MCP server prompt templates.

Reusable prompt templates exposed by the server. See MEMORY.md checklist: prompts.

The prompt handlers live in :mod:`server.prompts.prompts`, which exposes a
``register(mcp)`` function. :func:`register_all` is a thin, consistent wrapper so
the server entrypoint can wire tools, resources and prompts the same way.
"""

from __future__ import annotations

from . import prompts


def register_all(mcp) -> None:
    """Register every prompt template onto the given FastMCP server."""
    prompts.register(mcp)


__all__ = ["register_all"]
