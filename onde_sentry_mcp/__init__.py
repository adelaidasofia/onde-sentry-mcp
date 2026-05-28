"""onde-sentry-mcp — focused Sentry MCP server with PAT auth.

Tight tool surface (6 tools): whoami, list_projects, list_issues, get_issue,
list_alert_rules, create_alert_rule. Designed to pair with the Sentry context
shipped in onde-backend OND-741 — issues tagged service=mycelium_crm and
tagged with the lead_id-bearing mycelium_crm_lead context become directly
queryable + actionable from Claude.
"""

__version__ = "0.1.0"
