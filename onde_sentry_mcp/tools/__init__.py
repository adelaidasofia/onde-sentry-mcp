"""Tool modules. Each exports register(mcp) that wires its tools onto FastMCP."""

from __future__ import annotations

from fastmcp import FastMCP

from . import alerts, auth, issues, projects


def register_all(mcp: FastMCP) -> None:
    auth.register(mcp)
    projects.register(mcp)
    issues.register(mcp)
    alerts.register(mcp)
