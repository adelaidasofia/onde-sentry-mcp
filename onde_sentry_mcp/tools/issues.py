"""list_issues + get_issue — query and inspect Sentry issues."""

from __future__ import annotations

from fastmcp import FastMCP

from .._config import get_client, resolve_org, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def list_issues(
        query: str = "is:unresolved",
        org: str | None = None,
        project: str | None = None,
        limit: int = 25,
    ) -> list[dict]:
        """List issues in a project matching a Sentry query.

        `query` uses Sentry's search syntax. Tag filters: `service:mycelium_crm`,
        `error_class:MyceliumCRMError`, `lead_state:qualified`. Defaults to
        `is:unresolved`. `org` / `project` fall back to SENTRY_DEFAULT_ORG /
        SENTRY_DEFAULT_PROJECT env vars if unset. Use list_projects to discover
        valid project slugs.
        """
        return get_client().list_issues(
            org=resolve_org(org),
            project=resolve_project(project),
            query=query,
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def get_issue(issue_id: str) -> dict:
        """Fetch a single Sentry issue's full payload including tags + first event.

        `issue_id` is the numeric ID from a Sentry issue URL (e.g. 6789012345).
        Returns title, culprit, tags (incl. service, error_class, lead_state if
        set by onde-backend's push_scope wrapper), and the first event's
        breadcrumbs. Use list_issues to discover issue IDs.
        """
        return get_client().get_issue(issue_id)
