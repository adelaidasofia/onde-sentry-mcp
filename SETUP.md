# onde-sentry-mcp — setup

Three steps: install, set up the auth token, register with Claude Code.

## 1. Install

```bash
cd ~/dev/onde-sentry-mcp
uv sync --extra dev
```

Creates `.venv/` with `fastmcp`, `httpx`, and dev deps (`pytest`, `respx`, `ruff`).

Verify it boots:

```bash
.venv/bin/python -m pytest tests/        # 18 passed
.venv/bin/python -m onde_sentry_mcp.server < /dev/null  # exits immediately on closed stdin — that's fine
```

## 2. Create a Sentry User Auth Token

1. Open https://sentry.io/settings/account/api/auth-tokens/
2. Click **Create New Token**
3. Scopes required for the current tool set:
   - `org:read`
   - `project:read`
   - `project:write` (needed by `create_alert_rule`)
4. Copy the token (Sentry only shows it once).

## 3. Register with Claude Code

Add to `~/.claude/settings.json` under `mcpServers`. JSON does not expand `~`, so substitute your home dir (or the absolute clone path) in `command`:

```json
{
  "mcpServers": {
    "onde-sentry": {
      "command": "<absolute-path-to>/onde-sentry-mcp/.venv/bin/python",
      "args": ["-m", "onde_sentry_mcp.server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "<paste-token-here>",
        "SENTRY_DEFAULT_ORG": "<your-sentry-org-slug>",
        "SENTRY_DEFAULT_PROJECT": "<your-sentry-project-slug>"
      }
    }
  }
}
```

Or via CLI (shell expands `~`):

```bash
claude mcp add -s user \
  --env=SENTRY_AUTH_TOKEN=<paste-token-here> \
  --env=SENTRY_DEFAULT_ORG=<org-slug> \
  --env=SENTRY_DEFAULT_PROJECT=<project-slug> \
  onde-sentry -- ~/dev/onde-sentry-mcp/.venv/bin/python -m onde_sentry_mcp.server
```

Restart Claude Code so it picks up the new server.

## 4. Verify

In a Claude Code session, call:

```
whoami()
```

You should see your Sentry user + the API version. If you get `SentryConfigError: SENTRY_AUTH_TOKEN is unset`, the env var isn't being read — re-check the JSON.

If you get `Sentry API 401 ...`, the token doesn't have `org:read`. Re-create at https://sentry.io/settings/account/api/auth-tokens/.

## 5. Ship the OND-741 alert rule

Once `whoami` works:

```
list_alert_rules()              # confirm "Mycelium CRM push errors" doesn't already exist
list_projects()                 # confirm the project slug Sentry uses

create_alert_rule(
  name="Mycelium CRM push errors",
  filters=[
    {"id": "sentry.rules.filters.tagged_event.TaggedEventFilter",
     "key": "service", "match": "eq", "value": "mycelium_crm"}
  ],
  conditions=[
    {"id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
     "value": 5, "interval": "5m"}
  ],
  actions=[
    {"id": "sentry.mail.actions.NotifyEmailAction",
     "targetType": "Member", "targetIdentifier": <your-sentry-member-id>}
  ],
  filter_match="all",
  action_match="all",
  frequency=30
)
```

Add a Slack action as a second entry in `actions` if you've wired the Sentry → Slack integration:

```json
{"id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
 "workspace": "<slack-workspace-id-numeric>",
 "channel": "#alerts"}
```

## Tests

```bash
.venv/bin/python -m pytest tests/ -v       # 18 unit tests, mocked Sentry API via respx
.venv/bin/ruff check .                      # lint
```

## Token rotation

Rotate the User Auth Token by creating a new one at https://sentry.io/settings/account/api/auth-tokens/ and updating the `SENTRY_AUTH_TOKEN` value in `~/.claude/settings.json`. Restart Claude Code. Then revoke the old token from the same Sentry settings page.
