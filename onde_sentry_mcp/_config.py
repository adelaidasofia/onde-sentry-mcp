"""Env-driven config + lazy client singleton.

Reads the Sentry token + optional default org/project once per process so tools
don't have to plumb them through every call. The client is constructed lazily
on first use so module import never raises if the env isn't set yet — instead
the first tool call returns a SentryConfigError with the setup instructions.
"""

from __future__ import annotations

import os

from .client import SentryClient, SentryConfigError

TOKEN_ENV = "SENTRY_AUTH_TOKEN"
HOST_ENV = "SENTRY_HOST"
DEFAULT_ORG_ENV = "SENTRY_DEFAULT_ORG"
DEFAULT_PROJECT_ENV = "SENTRY_DEFAULT_PROJECT"

_client: SentryClient | None = None


def get_client() -> SentryClient:
    """Return the process-wide SentryClient. Raises SentryConfigError if unset."""
    global _client
    if _client is None:
        token = os.environ.get(TOKEN_ENV, "")
        host = os.environ.get(HOST_ENV, "https://sentry.io")
        _client = SentryClient(token=token, host=host)
    return _client


def resolve_org(arg: str | None) -> str:
    """Caller arg wins; else fall back to SENTRY_DEFAULT_ORG."""
    org = arg or os.environ.get(DEFAULT_ORG_ENV, "")
    if not org:
        raise SentryConfigError(
            f"No org given. Pass `org` as a tool argument or set {DEFAULT_ORG_ENV}=<your-sentry-org-slug>."
        )
    return org


def resolve_project(arg: str | None) -> str:
    """Caller arg wins; else fall back to SENTRY_DEFAULT_PROJECT."""
    project = arg or os.environ.get(DEFAULT_PROJECT_ENV, "")
    if not project:
        raise SentryConfigError(
            "No project given. Pass `project` as a tool argument or set "
            f"{DEFAULT_PROJECT_ENV}=<your-sentry-project-slug>."
        )
    return project


def reset_for_tests() -> None:
    """Drop the singleton — tests use this to pick up monkeypatched env."""
    global _client
    _client = None
