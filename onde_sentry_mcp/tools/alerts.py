"""list_alert_rules + create_alert_rule — manage Sentry Issue Alert rules."""

from __future__ import annotations

from fastmcp import FastMCP

from .._config import get_client, resolve_org, resolve_project


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def list_alert_rules(
        org: str | None = None,
        project: str | None = None,
    ) -> list[dict]:
        """List Issue Alert rules configured in a Sentry project.

        Use this BEFORE create_alert_rule to check the rule isn't already there
        (creates are not idempotent on Sentry's side — calling twice creates
        two rules). `org` / `project` fall back to SENTRY_DEFAULT_ORG /
        SENTRY_DEFAULT_PROJECT env vars if unset.
        """
        return get_client().list_alert_rules(
            org=resolve_org(org),
            project=resolve_project(project),
        )

    @mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    def create_alert_rule(
        name: str,
        conditions: list[dict],
        actions: list[dict],
        filters: list[dict] | None = None,
        action_match: str = "all",
        filter_match: str = "all",
        frequency: int = 30,
        org: str | None = None,
        project: str | None = None,
    ) -> dict:
        """Create a Sentry Issue Alert rule in a project.

        NOT idempotent — call list_alert_rules first to avoid duplicates.

        `conditions` are list items like
          {"id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
           "value": 5, "interval": "5m"}.

        `filters` (optional) are list items like
          {"id": "sentry.rules.filters.tagged_event.TaggedEventFilter",
           "key": "service", "match": "eq", "value": "mycelium_crm"}.

        `actions` are list items like
          {"id": "sentry.mail.actions.NotifyEmailAction",
           "targetType": "Member", "targetIdentifier": <user_id>}
          or
          {"id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
           "workspace": "<slack_workspace_id>", "channel": "#alerts"}.

        `action_match` / `filter_match` are "all" | "any" | "none".
        `frequency` is minutes between repeated firings of the same rule.

        Full param reference:
        https://docs.sentry.io/api/projects/create-an-issue-alert-rule-for-a-project/
        """
        return get_client().create_alert_rule(
            org=resolve_org(org),
            project=resolve_project(project),
            name=name,
            conditions=conditions,
            actions=actions,
            filters=filters,
            action_match=action_match,
            filter_match=filter_match,
            frequency=frequency,
        )
