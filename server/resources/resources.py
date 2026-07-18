"""Resource providers.

MEMORY.md checklist: MCP Server resources -> README, config, files.

Where tools are *actions* the client invokes, **resources** are *readable data*
the client can fetch by URI (think of them like GET endpoints). We expose three:

* ``docs://readme``      -- the project README.
* ``config://server``    -- the effective (secret-free) server configuration.
* ``files://{name}``     -- a templated resource for reading a sandboxed file.

The ``files://{name}`` form shows a *resource template*: the ``{name}`` segment
is filled in by the client, and FastMCP routes it to our handler.
"""

from __future__ import annotations

import json
from pathlib import Path

from server.tools.file_reader import list_files, read_file

# Repo root = two parents up from this file (server/resources/resources.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_readme() -> str:
    """Return the project README text (or a placeholder if missing)."""
    readme = _REPO_ROOT / "README.md"
    if readme.exists():
        return readme.read_text(encoding="utf-8", errors="replace")
    return "# mcp-server-client\n\n(README.md not found.)"


def _effective_config() -> dict:
    """Return the effective server config with any secrets stripped out.

    We load ``config/config.json`` if present, otherwise the shipped example, and
    then blank out any obvious secret fields so we never leak them over MCP.
    """
    config_dir = _REPO_ROOT / "config"
    chosen = config_dir / "config.json"
    if not chosen.exists():
        chosen = config_dir / "config.example.json"

    try:
        data = json.loads(chosen.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    # Redact secret-looking values before exposing the config.
    for tool_cfg in data.get("tools", {}).values():
        for secret_key in ("api_key", "token", "connection_string"):
            if secret_key in tool_cfg:
                tool_cfg[secret_key] = "***redacted***"
    return data


def register(mcp) -> None:
    """Register the README, config and files resources on the FastMCP server."""

    @mcp.resource("docs://readme", mime_type="text/markdown")
    def readme_resource() -> str:
        """The project README, exposed as a readable MCP resource."""
        return _read_readme()

    @mcp.resource("config://server", mime_type="application/json")
    def config_resource() -> str:
        """The effective server configuration (secrets redacted)."""
        return json.dumps(_effective_config(), indent=2)

    @mcp.resource("files://list", mime_type="application/json")
    def files_list_resource() -> str:
        """A JSON list of files available under the sandboxed data directory."""
        return json.dumps(list_files(), indent=2)

    @mcp.resource("files://{name}", mime_type="text/plain")
    def file_resource(name: str) -> str:
        """Read a single sandboxed file by name (templated resource)."""
        return read_file(name)
