"""HTTP client for the Sentry REST API.

Thin httpx wrapper. One client instance per process (FastMCP server lifecycle).
Maps HTTP failures to typed exceptions so tools can return structured MCP
errors instead of crashing the transport.

Auth: User Auth Token (NOT OAuth). Scopes required for the current tool set:
  org:read, project:read, project:write
Generate at https://sentry.io/settings/account/api/auth-tokens/.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

DEFAULT_HOST = "https://sentry.io"
DEFAULT_TIMEOUT_SECONDS = 15.0


class SentryError(Exception):
    """A Sentry API call failed at the wire layer (4xx/5xx, transport)."""


class SentryConfigError(SentryError):
    """Required configuration (token, org) is missing. Not retryable."""


class SentryClient:
    """Synchronous Sentry REST API client.

    Sync (not async) on purpose: FastMCP tool handlers can be sync or async,
    and Sentry's per-request latency is small. Sync keeps the call site
    simpler for tool authors.
    """

    def __init__(
        self,
        token: str,
        host: str = DEFAULT_HOST,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not token:
            raise SentryConfigError(
                "SENTRY_AUTH_TOKEN is unset. Create a User Auth Token at "
                "https://sentry.io/settings/account/api/auth-tokens/ with scopes "
                "org:read, project:read, project:write."
            )
        self.token = token
        self.base_url = host.rstrip("/") + "/api/0"
        self._timeout = timeout

    # --- internal --------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> Any:
        url = self.base_url + path
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": "onde-sentry-mcp/0.1",
        }
        if json is not None:
            headers["Content-Type"] = "application/json"

        with httpx.Client(timeout=self._timeout) as c:
            r = c.request(method, url, params=params, json=json, headers=headers)

        if r.status_code >= 400:
            detail = ""
            try:
                body = r.json()
                detail = body.get("detail") or str(body)
            except Exception:
                detail = (r.text or "")[:200]
            raise SentryError(f"Sentry API {r.status_code} on {method} {path}: {detail}")

        # 204 No Content is valid for some mutations
        if r.status_code == 204 or not r.content:
            return None
        return r.json()

    # --- tools ------------------------------------------------------

    def whoami(self) -> dict:
        """GET /api/0/ — returns the root payload, including the authed user."""
        return self._request("GET", "/")

    def list_projects(self, org: str) -> list[dict]:
        """GET /api/0/organizations/{org}/projects/ — projects visible to the token."""
        return self._request("GET", f"/organizations/{org}/projects/")

    def list_issues(
        self,
        org: str,
        project: str,
        query: str = "is:unresolved",
        limit: int = 100,
    ) -> list[dict]:
        """GET /api/0/projects/{org}/{project}/issues/ — supports Sentry query syntax.

        Default `is:unresolved` matches the Sentry UI default. Tag filters use
        `key:value` syntax (e.g. `service:mycelium_crm`).
        """
        return self._request(
            "GET",
            f"/projects/{org}/{project}/issues/",
            params={"query": query, "limit": limit},
        )

    def get_issue(self, issue_id: str) -> dict:
        """GET /api/0/issues/{id}/ — full issue payload incl. tags + first event."""
        return self._request("GET", f"/issues/{issue_id}/")

    def list_alert_rules(self, org: str, project: str) -> list[dict]:
        """GET /api/0/projects/{org}/{project}/rules/ — Issue Alert rules in project."""
        return self._request("GET", f"/projects/{org}/{project}/rules/")

    def create_alert_rule(
        self,
        org: str,
        project: str,
        name: str,
        conditions: list[dict],
        actions: list[dict],
        filters: list[dict] | None = None,
        action_match: str = "all",
        filter_match: str = "all",
        frequency: int = 30,
    ) -> dict:
        """POST /api/0/projects/{org}/{project}/rules/ — create an Issue Alert.

        `frequency` is minutes between repeated firings of the same rule on the
        same issue. `action_match` / `filter_match` are "all" | "any" | "none".
        See https://docs.sentry.io/api/projects/create-an-issue-alert-rule-for-a-project/.
        """
        payload = {
            "name": name,
            "actionMatch": action_match,
            "filterMatch": filter_match,
            "conditions": conditions,
            "filters": filters or [],
            "actions": actions,
            "frequency": frequency,
        }
        return self._request(
            "POST",
            f"/projects/{org}/{project}/rules/",
            json=payload,
        )
