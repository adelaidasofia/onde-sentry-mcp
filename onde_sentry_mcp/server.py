"""onde-sentry-mcp FastMCP entry point.

Run with: python -m onde_sentry_mcp.server  (or via the `onde-sentry-mcp`
console script after install.)

Tools register at import time. The Sentry client is constructed lazily on the
first tool call so a missing SENTRY_AUTH_TOKEN doesn't crash the boot — it
just surfaces a clear SentryConfigError on the first call.
"""

from __future__ import annotations

import logging
import os
import sys

from fastmcp import FastMCP

from . import __version__
from .tools import register_all

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("onde-sentry-mcp")

mcp = FastMCP(
    name="onde-sentry-mcp",
    instructions=(
        "Sentry MCP scoped for Onde debugging + alert-rule provisioning. "
        "Always call whoami first to confirm auth, then list_projects to discover "
        "project slugs. For alert-rule creation, call list_alert_rules FIRST to "
        "avoid duplicates — create_alert_rule is NOT idempotent on Sentry's side."
    ),
)

register_all(mcp)


def _startup_log() -> None:
    log.info("onde-sentry-mcp v%s starting", __version__)
    token_set = bool(os.environ.get("SENTRY_AUTH_TOKEN"))
    log.info("SENTRY_AUTH_TOKEN: %s", "set" if token_set else "UNSET (whoami will fail until set)")
    org = os.environ.get("SENTRY_DEFAULT_ORG", "")
    project = os.environ.get("SENTRY_DEFAULT_PROJECT", "")
    if org:
        log.info("SENTRY_DEFAULT_ORG=%s", org)
    if project:
        log.info("SENTRY_DEFAULT_PROJECT=%s", project)


_startup_log()


def main() -> None:
    """Console-script entry point — runs the MCP over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
