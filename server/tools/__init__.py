"""MCP server tools.

Each module registers one tool exposed by the server. See MEMORY.md checklist:
calculator, weather, file_reader, github, database, notes.

Every tool module exposes a ``register(mcp)`` function. :func:`register_all`
wires all of them onto a FastMCP instance in one call, keeping the server
entrypoint a thin layer.
"""

from __future__ import annotations

from . import calculator, database, file_reader, github, notes, weather

# Ordered so the server advertises tools in a stable, readable sequence.
_MODULES = (calculator, weather, file_reader, github, database, notes)


def register_all(mcp) -> None:
    """Register every tool module onto the given FastMCP server."""
    for module in _MODULES:
        module.register(mcp)


__all__ = ["register_all"]
