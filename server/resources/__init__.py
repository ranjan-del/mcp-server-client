"""MCP server resources.

Exposes readable resources over MCP. See MEMORY.md checklist: README, config, files.

The resource handlers live in :mod:`server.resources.resources`, which exposes a
``register(mcp)`` function. :func:`register_all` is a thin, consistent wrapper so
the server entrypoint can wire tools, resources and prompts the same way.
"""

from __future__ import annotations

from . import resources


def register_all(mcp) -> None:
    """Register every resource onto the given FastMCP server."""
    resources.register(mcp)


__all__ = ["register_all"]
