"""MCP Server package.

Exposes tools, resources, and prompt templates over the Model Context Protocol.
The server factory lives in :mod:`server.server` (imported lazily by callers to
avoid a circular import at package initialisation)::

    from server.server import build_server

See MEMORY.md checklist for the full scope.
"""

__all__: list[str] = []
