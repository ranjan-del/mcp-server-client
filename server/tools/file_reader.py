"""File reader tool.

MEMORY.md checklist: MCP Server tools -> file reader.

Sandboxing design
------------------
Reading files on behalf of an untrusted caller is dangerous: without care a
request for ``../../etc/passwd`` (or an absolute path, or a symlink pointing
outside the tree) would leak arbitrary files. The defence here is a **base
directory sandbox**:

1. Resolve the base directory to a canonical absolute path (``resolve()`` also
   collapses ``..`` and follows symlinks).
2. Resolve the requested path *relative to that base*.
3. Verify the resolved target is still inside the base using
   ``Path.is_relative_to``. If it escaped, refuse.

Because we compare the fully-resolved paths, ``..`` traversal, absolute paths
and symlink escapes are all rejected by the same single check.
"""

from __future__ import annotations

from pathlib import Path


class FileAccessError(Exception):
    """Raised when a requested path is outside the sandbox or cannot be read."""


def _default_base_dir() -> Path:
    """The default sandbox root: the ``data/`` directory beside the repo root."""
    # server/tools/file_reader.py -> repo root is three parents up.
    return (Path(__file__).resolve().parents[2] / "data").resolve()


def read_file(relative_path: str, base_dir: str | Path | None = None,
              max_bytes: int = 1_000_000) -> str:
    """Read a text file located inside ``base_dir`` and return its contents.

    ``relative_path`` is always interpreted relative to ``base_dir``; any attempt
    to escape the sandbox (via ``..``, an absolute path or a symlink) raises
    :class:`FileAccessError`.
    """
    base = Path(base_dir).resolve() if base_dir is not None else _default_base_dir()

    # Join then fully resolve. resolve() collapses ".." and follows symlinks, so
    # the escape check below sees the *real* target location.
    candidate = (base / relative_path).resolve()

    # The single security check: the resolved target must live under the base.
    if not candidate.is_relative_to(base):
        raise FileAccessError(
            f"Access denied: {relative_path!r} resolves outside the sandbox"
        )

    if not candidate.exists():
        raise FileAccessError(f"File not found: {relative_path!r}")
    if not candidate.is_file():
        raise FileAccessError(f"Not a regular file: {relative_path!r}")

    # Guard against reading something enormous into memory.
    size = candidate.stat().st_size
    if size > max_bytes:
        raise FileAccessError(
            f"File too large ({size} bytes > {max_bytes} byte limit)"
        )

    return candidate.read_text(encoding="utf-8", errors="replace")


def list_files(base_dir: str | Path | None = None) -> list[str]:
    """List the files available inside the sandbox (relative paths)."""
    base = Path(base_dir).resolve() if base_dir is not None else _default_base_dir()
    if not base.exists():
        return []
    return sorted(
        str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()
    )


def register(mcp) -> None:
    """Expose the sandboxed file reader as MCP tools on the FastMCP server."""

    @mcp.tool()
    def file_reader(relative_path: str) -> str:
        """Read a text file from the server's sandboxed data directory.

        Path traversal outside the sandbox is rejected.
        """
        return read_file(relative_path)

    @mcp.tool()
    def file_list() -> list[str]:
        """List the files available in the server's sandboxed data directory."""
        return list_files()
