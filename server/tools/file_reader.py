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

Streaming
---------
This module is also where the project demonstrates MCP **progress
notifications**. :func:`iter_file_chunks` reads the file in fixed-size pieces
instead of one gulp, which gives the MCP tool something to report progress
*about* while it works. See :func:`register` for the reporting side and
``client/client.py`` for the receiving side.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple

# Imported at module scope on purpose: `from __future__ import annotations` turns
# the `ctx: Context` annotation in register() into a string, and FastMCP resolves
# that string against this module's globals. A function-local import would not be
# visible there and tool registration would fail.
from mcp.server.fastmcp import Context

# Default streaming chunk size. Deliberately small (not a tuned I/O buffer) so a
# tiny demo file still produces several progress notifications to look at.
DEFAULT_CHUNK_SIZE = 32


class FileAccessError(Exception):
    """Raised when a requested path is outside the sandbox or cannot be read."""


def _default_base_dir() -> Path:
    """The default sandbox root: the ``data/`` directory beside the repo root."""
    # server/tools/file_reader.py -> repo root is three parents up.
    return (Path(__file__).resolve().parents[2] / "data").resolve()


def _safe_target(relative_path: str, base_dir: str | Path | None,
                 max_bytes: int) -> Path:
    """Resolve ``relative_path`` inside the sandbox or raise :class:`FileAccessError`.

    Factored out of :func:`read_file` so the streaming reader below enforces the
    exact same security checks. One implementation means one place to get right.
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

    return candidate


def read_file(relative_path: str, base_dir: str | Path | None = None,
              max_bytes: int = 1_000_000) -> str:
    """Read a text file located inside ``base_dir`` and return its contents.

    ``relative_path`` is always interpreted relative to ``base_dir``; any attempt
    to escape the sandbox (via ``..``, an absolute path or a symlink) raises
    :class:`FileAccessError`.
    """
    candidate = _safe_target(relative_path, base_dir, max_bytes)
    return candidate.read_text(encoding="utf-8", errors="replace")


def iter_file_chunks(relative_path: str, base_dir: str | Path | None = None,
                     chunk_size: int = DEFAULT_CHUNK_SIZE,
                     max_bytes: int = 1_000_000) -> Iterator[Tuple[str, int, int]]:
    """Yield ``(chunk_text, chars_read_so_far, total_chars)`` for a sandboxed file.

    The same sandbox checks as :func:`read_file` apply. Yielding the running and
    total counts alongside each chunk is what lets the MCP tool turn a plain read
    into a stream of progress notifications without the caller doing any
    bookkeeping.

    Note the counts are in *characters*, not bytes: we decode as we go, and a
    progress bar built on decoded length is the one that matches what the caller
    finally receives.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    candidate = _safe_target(relative_path, base_dir, max_bytes)
    text = candidate.read_text(encoding="utf-8", errors="replace")
    total = len(text)

    # An empty file still yields one (empty) chunk so consumers always see at
    # least one progress event and never divide by an unset total.
    if total == 0:
        yield "", 0, 0
        return

    for start in range(0, total, chunk_size):
        chunk = text[start:start + chunk_size]
        yield chunk, start + len(chunk), total


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
    async def file_reader(relative_path: str, ctx: Context) -> str:
        """Read a text file from the server's sandboxed data directory.

        Streams progress notifications as it reads, and rejects path traversal
        outside the sandbox.
        """
        # FastMCP recognises the `ctx: Context` parameter, injects it, and hides
        # it from the tool's public JSON schema, so callers still just pass
        # `relative_path`.
        pieces: list[str] = []
        for chunk, read_so_far, total in iter_file_chunks(relative_path):
            pieces.append(chunk)
            # report_progress emits a `notifications/progress` message on the
            # same connection while the call is still in flight. That is what
            # "streaming" means in MCP: the result arrives once, but the client
            # can watch the work happen.
            await ctx.report_progress(
                progress=read_so_far,
                total=total,
                message=f"read {read_so_far}/{total} chars of {relative_path}",
            )
        return "".join(pieces)

    @mcp.tool()
    def file_list() -> list[str]:
        """List the files available in the server's sandboxed data directory."""
        return list_files()
