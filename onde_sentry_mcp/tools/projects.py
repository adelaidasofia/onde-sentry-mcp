"""list_projects — discover project slugs in an org."""

from __future__ import annotations

from fastmcp import FastMCP

from .._config import get_client, resolve_org


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def list_projects(org: str | None = None) -> list[dict]:
        """List Sentry projects visible to the token.

        Call this to find the project slug needed by list_issues, get_issue,
        list_alert_rules, and create_alert_rule. `org` defaults to the
        SENTRY_DEFAULT_ORG env var if unset.
        """
        return get_client().list_projects(resolve_org(org))
