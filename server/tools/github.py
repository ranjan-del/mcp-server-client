"""GitHub tool.

MEMORY.md checklist: MCP Server tools -> github.

Offline-first design
--------------------
By default this returns a **deterministic offline stub** describing a public
repo, so the tool and its tests need no network access and no token. If the
``GITHUB_TOKEN`` environment variable is set, :func:`get_repo_info` instead
queries the real GitHub REST API (``/repos/{owner}/{repo}``) and falls back to
the stub on any error.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict


def _deterministic_repo(owner: str, repo: str) -> Dict[str, Any]:
    """Return a stable, made-up description of ``owner/repo``.

    Star/fork counts are derived from a hash of ``owner/repo`` so the same repo
    always looks the same -- reproducible for tests and demos.
    """
    full_name = f"{owner}/{repo}"
    seed = int(hashlib.sha256(full_name.lower().encode("utf-8")).hexdigest(), 16)

    return {
        "full_name": full_name,
        "source": "offline-stub",
        "description": f"Stub description for {full_name}",
        "stars": seed % 50_000,
        "forks": seed % 5_000,
        "open_issues": seed % 500,
        "language": ["Python", "TypeScript", "Go", "Rust", "Java"][seed % 5],
        "html_url": f"https://github.com/{full_name}",
    }


def get_repo_info(owner: str, repo: str) -> Dict[str, Any]:
    """Return basic info about a public GitHub repository.

    Uses the offline stub by default; uses the live GitHub API when
    ``GITHUB_TOKEN`` is set, degrading gracefully back to the stub on error.
    """
    if not owner or not repo:
        raise ValueError("owner and repo must both be provided")

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            return _get_repo_info_live(owner, repo, token)
        except Exception:  # noqa: BLE001 - graceful degradation is intentional
            pass

    return _deterministic_repo(owner, repo)


def _get_repo_info_live(owner: str, repo: str, token: str) -> Dict[str, Any]:
    """Optional real lookup against the GitHub REST API (needs GITHUB_TOKEN)."""
    import httpx  # local import: only needed on the optional live path

    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = httpx.get(url, headers=headers, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    return {
        "full_name": data["full_name"],
        "source": "api.github.com",
        "description": data.get("description") or "",
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "language": data.get("language") or "unknown",
        "html_url": data["html_url"],
    }


def register(mcp) -> None:
    """Expose :func:`get_repo_info` as an MCP tool on the given FastMCP server."""

    @mcp.tool()
    def github(owner: str, repo: str) -> Dict[str, Any]:
        """Fetch basic public info about a GitHub repository (owner/repo).

        Returns a deterministic offline stub unless GITHUB_TOKEN is set.
        """
        return get_repo_info(owner, repo)
