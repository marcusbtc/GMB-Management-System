"""Thin MCP server for Google Business Profile, wrapping existing Google clients."""

from src.gmb_mcp.server import TOOL_NAMES, create_mcp, main

__all__ = ["TOOL_NAMES", "create_mcp", "main"]
