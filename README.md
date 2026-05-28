# onde-sentry-mcp

A focused Python MCP server for the Sentry REST API, scoped for Onde debugging + alert-rule provisioning.

Born out of the OND-741 push to wire onde-backend's Mycelium CRM push into Sentry's tag + context surface — once the backend tagged events with `service=mycelium_crm` + `tenant=onde` + `lead_id`, the missing piece was a Claude-side tool that could query those events and provision the alert rule. This MCP closes that gap.

## Why a focused MCP, not the official Sentry one

Sentry ships an [official MCP](https://mcp.sentry.dev). It's broader (~30 tools, full Seer integration). This one is intentionally smaller — six tools, one job each, easier to reason about when troubleshooting a single Onde error path.

| Tool | Read/Write | Purpose |
|---|---|---|
| `whoami` | Read | Probe the token is wired correctly |
| `list_projects` | Read | Discover project slugs |
| `list_issues` | Read | Query issues by Sentry tag syntax (`service:mycelium_crm`) |
| `get_issue` | Read | Full payload incl. tags + first event breadcrumbs |
| `list_alert_rules` | Read | Inspect existing rules before creating new ones |
| `create_alert_rule` | Write | Provision an Issue Alert (NOT idempotent) |

## Install

See [SETUP.md](SETUP.md) for the Claude Code wiring + token-creation walk-through.

## License

MIT
