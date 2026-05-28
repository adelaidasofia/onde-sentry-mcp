"""Smoke tests: every module imports, every tool registers on a fresh FastMCP.

Mirrors the linear-mcp pattern (the canonical reference MCP in ~/dev/).
"""

from __future__ import annotations


def test_package_imports() -> None:
    import onde_sentry_mcp  # noqa: F401

    assert onde_sentry_mcp.__version__


def test_submodules_import() -> None:
    from onde_sentry_mcp import client, server  # noqa: F401
    from onde_sentry_mcp.tools import alerts, auth, issues, projects  # noqa: F401


def test_tools_register_on_fresh_fastmcp(monkeypatch) -> None:
    """All tool modules wire onto a fresh FastMCP without error.

    Uses a dummy token so the client constructs successfully; no network is hit
    because no tool is actually called.
    """
    monkeypatch.setenv("SENTRY_AUTH_TOKEN", "test-token-not-real")

    from fastmcp import FastMCP

    from onde_sentry_mcp.tools import register_all

    mcp = FastMCP("onde-sentry-mcp-test")
    register_all(mcp)
