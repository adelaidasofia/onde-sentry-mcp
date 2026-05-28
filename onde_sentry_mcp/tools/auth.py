"""Auth probe — confirms the SENTRY_AUTH_TOKEN is wired correctly."""

from __future__ import annotations

from fastmcp import FastMCP

from .._config import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def whoami() -> dict:
        """Probe the Sentry API root and return the authed identity.

        Use this FIRST when setting up the MCP — confirms the SENTRY_AUTH_TOKEN
        env var is set and has at least org:read scope. Returns the Sentry API
        version plus the User Auth Token's owner.
        """
        return get_client().whoami()
