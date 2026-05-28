"""SentryClient unit tests.

Mocks the Sentry REST API with respx so we exercise the real client behavior
(URL construction, auth headers, error mapping) without hitting sentry.io.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from onde_sentry_mcp.client import (
    SentryClient,
    SentryConfigError,
    SentryError,
)

# --- Construction ----------------------------------------------------


def test_client_requires_token() -> None:
    with pytest.raises(SentryConfigError):
        SentryClient(token="")


def test_client_accepts_token() -> None:
    client = SentryClient(token="dummy")
    assert client.token == "dummy"


def test_client_defaults_host_to_sentry_io() -> None:
    client = SentryClient(token="dummy")
    assert client.base_url == "https://sentry.io/api/0"


def test_client_strips_trailing_slash_from_host() -> None:
    client = SentryClient(token="dummy", host="https://sentry.io/")
    assert client.base_url == "https://sentry.io/api/0"


# --- Auth header ----------------------------------------------------


@respx.mock
def test_request_sends_bearer_auth_header() -> None:
    route = respx.get("https://sentry.io/api/0/").mock(return_value=httpx.Response(200, json={"version": "1.0"}))
    SentryClient(token="my-secret").whoami()
    auth = route.calls.last.request.headers.get("Authorization")
    assert auth == "Bearer my-secret"


# --- whoami ----------------------------------------------------------


@respx.mock
def test_whoami_returns_root_payload() -> None:
    respx.get("https://sentry.io/api/0/").mock(
        return_value=httpx.Response(
            200,
            json={"version": "1.0", "user": {"email": "a@b.com"}},
        )
    )
    result = SentryClient(token="dummy").whoami()
    assert result["user"]["email"] == "a@b.com"


# --- list_projects ---------------------------------------------------


@respx.mock
def test_list_projects_hits_org_endpoint() -> None:
    route = respx.get("https://sentry.io/api/0/organizations/onde/projects/").mock(
        return_value=httpx.Response(200, json=[{"slug": "onde-backend"}])
    )

    result = SentryClient(token="dummy").list_projects(org="onde")

    assert route.called
    assert result[0]["slug"] == "onde-backend"


# --- list_issues -----------------------------------------------------


@respx.mock
def test_list_issues_passes_query_param() -> None:
    route = respx.get("https://sentry.io/api/0/projects/onde/onde-backend/issues/").mock(
        return_value=httpx.Response(200, json=[])
    )

    SentryClient(token="dummy").list_issues(
        org="onde",
        project="onde-backend",
        query="service:mycelium_crm",
    )

    assert route.called
    assert route.calls.last.request.url.params["query"] == "service:mycelium_crm"


@respx.mock
def test_list_issues_default_query_is_unresolved() -> None:
    """Sentry's UI default is `is:unresolved` — match that for least-surprise."""
    route = respx.get("https://sentry.io/api/0/projects/onde/onde-backend/issues/").mock(
        return_value=httpx.Response(200, json=[])
    )

    SentryClient(token="dummy").list_issues(org="onde", project="onde-backend")

    assert route.calls.last.request.url.params["query"] == "is:unresolved"


@respx.mock
def test_list_issues_respects_limit() -> None:
    route = respx.get("https://sentry.io/api/0/projects/onde/onde-backend/issues/").mock(
        return_value=httpx.Response(200, json=[])
    )

    SentryClient(token="dummy").list_issues(org="onde", project="onde-backend", limit=25)

    assert route.calls.last.request.url.params["limit"] == "25"


# --- get_issue -------------------------------------------------------


@respx.mock
def test_get_issue_returns_full_payload_with_tags() -> None:
    respx.get("https://sentry.io/api/0/issues/12345/").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "12345",
                "title": "Mycelium CRM machine-intake 502 for Lead ...",
                "tags": [
                    {"key": "service", "value": "mycelium_crm"},
                    {"key": "error_class", "value": "MyceliumCRMError"},
                ],
            },
        )
    )

    result = SentryClient(token="dummy").get_issue(issue_id="12345")

    assert result["id"] == "12345"
    assert {"key": "error_class", "value": "MyceliumCRMError"} in result["tags"]


# --- list_alert_rules ------------------------------------------------


@respx.mock
def test_list_alert_rules_hits_project_rules_endpoint() -> None:
    route = respx.get("https://sentry.io/api/0/projects/onde/onde-backend/rules/").mock(
        return_value=httpx.Response(200, json=[{"id": "111", "name": "rule"}])
    )

    result = SentryClient(token="dummy").list_alert_rules(org="onde", project="onde-backend")

    assert route.called
    assert result[0]["id"] == "111"


# --- create_alert_rule -----------------------------------------------


@respx.mock
def test_create_alert_rule_posts_full_payload() -> None:
    route = respx.post("https://sentry.io/api/0/projects/onde/onde-backend/rules/").mock(
        return_value=httpx.Response(
            201,
            json={"id": "888", "name": "Mycelium CRM push errors"},
        )
    )

    result = SentryClient(token="dummy").create_alert_rule(
        org="onde",
        project="onde-backend",
        name="Mycelium CRM push errors",
        action_match="all",
        filter_match="all",
        conditions=[
            {
                "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
                "value": 5,
                "interval": "5m",
            }
        ],
        filters=[
            {
                "id": "sentry.rules.filters.tagged_event.TaggedEventFilter",
                "key": "service",
                "match": "eq",
                "value": "mycelium_crm",
            }
        ],
        actions=[
            {
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "Member",
                "targetIdentifier": 12345,
            }
        ],
        frequency=5,
    )

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.read())
    assert body["name"] == "Mycelium CRM push errors"
    assert body["actionMatch"] == "all"
    assert body["filterMatch"] == "all"
    assert body["frequency"] == 5
    assert body["conditions"][0]["interval"] == "5m"
    assert body["filters"][0]["value"] == "mycelium_crm"
    assert result["id"] == "888"


# --- Error handling --------------------------------------------------


@respx.mock
def test_401_raises_sentry_error_with_status() -> None:
    respx.get("https://sentry.io/api/0/").mock(return_value=httpx.Response(401, json={"detail": "Invalid token"}))
    with pytest.raises(SentryError) as exc:
        SentryClient(token="bad").whoami()
    assert "401" in str(exc.value)


@respx.mock
def test_500_raises_sentry_error() -> None:
    respx.get("https://sentry.io/api/0/").mock(return_value=httpx.Response(500, text="Server error"))
    with pytest.raises(SentryError) as exc:
        SentryClient(token="dummy").whoami()
    assert "500" in str(exc.value)
