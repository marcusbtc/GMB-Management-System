"""MCP entrypoint for Google Business Profile.

stdio is the default (Cursor / Claude Desktop). Optional Streamable HTTP
uses the same tools. Google calls are delegated to data_fetcher / drive_helper.
"""

import argparse
import os
from typing import Any

from src.gmb_mcp import auth, tools

READ_TOOLS = (
    "list_accounts",
    "list_locations",
    "get_daily_metrics",
    "get_search_keywords",
    "list_reviews",
    "list_posts",
    "list_media",
    "list_questions",
    "profile_health_check",
)
WRITE_TOOLS = (
    "create_local_post",
    "upload_image_to_drive",
    "reply_to_review",
)
AUTH_TOOLS = (
    "start_oauth",
    "complete_oauth",
)
TOOL_NAMES = READ_TOOLS + WRITE_TOOLS + AUTH_TOOLS

DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 8765
HTTP_MAX_BODY_BYTES = 15 * 1024 * 1024


def _mcp_server_class():
    try:
        from mcp.server.fastmcp import FastMCP

        return FastMCP
    except ImportError:
        from mcp.server import MCPServer

        return MCPServer


def create_mcp():
    """Builds the MCP server with GBP tools. Safe to import (does not serve)."""
    server_cls = _mcp_server_class()
    instructions = (
        "Google Business Profile MCP. Tools return JSON only. "
        "Authenticate with access_token, GOOGLE_ACCESS_TOKEN, a gitignored "
        "token file, or start_oauth + complete_oauth. Never echo tokens."
    )
    try:
        mcp = server_cls("google-business-profile", instructions=instructions)
    except TypeError:
        mcp = server_cls("google-business-profile")

    @mcp.tool()
    def list_accounts(access_token: str | None = None) -> dict[str, Any]:
        """List Google Business Profile accounts for the authenticated user."""
        return tools.list_accounts(auth.resolve_credentials(access_token))

    @mcp.tool()
    def list_locations(
        account_name: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """List locations. account_name is accounts/{accountId}, or omit for all."""
        return tools.list_locations(auth.resolve_credentials(access_token), account_name)

    @mcp.tool()
    def get_daily_metrics(
        location_id: str,
        start_date: str,
        end_date: str,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Daily performance metrics. Dates are YYYY-MM-DD. location_id accepts v1 or v4 paths."""
        return tools.get_daily_metrics(
            auth.resolve_credentials(access_token),
            location_id,
            start_date,
            end_date,
        )

    @mcp.tool()
    def get_search_keywords(
        location_id: str,
        start_date: str,
        end_date: str,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Monthly search keyword impressions. Dates are YYYY-MM-DD."""
        return tools.get_search_keywords(
            auth.resolve_credentials(access_token),
            location_id,
            start_date,
            end_date,
        )

    @mcp.tool()
    def list_reviews(
        location_id: str,
        account_name: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """List reviews for a location. Uses resolve_location_parent for v1 vs v4 paths."""
        return tools.list_reviews(
            auth.resolve_credentials(access_token),
            location_id,
            account_name,
        )

    @mcp.tool()
    def list_posts(
        location_id: str,
        account_name: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """List local posts for a location."""
        return tools.list_posts(
            auth.resolve_credentials(access_token),
            location_id,
            account_name,
        )

    @mcp.tool()
    def list_media(
        location_id: str,
        account_name: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """List media items for a location."""
        return tools.list_media(
            auth.resolve_credentials(access_token),
            location_id,
            account_name,
        )

    @mcp.tool()
    def list_questions(
        location_id: str,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """List Q&A questions for a location (mybusinessquestions v1)."""
        return tools.list_questions(auth.resolve_credentials(access_token), location_id)

    @mcp.tool()
    def profile_health_check(
        location_id: str,
        account_name: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Run the existing profile health analysis and return JSON check results."""
        return tools.profile_health_check(
            auth.resolve_credentials(access_token),
            location_id,
            account_name,
        )

    @mcp.tool()
    def create_local_post(
        location_id: str,
        summary: str,
        account_name: str | None = None,
        topic_type: str = "STANDARD",
        language_code: str = "pt-BR",
        cta_type: str | None = None,
        cta_url: str | None = None,
        image_url: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Create a Google Business Profile local post (STANDARD, OFFER, or EVENT)."""
        return tools.create_local_post(
            auth.resolve_credentials(access_token),
            location_id,
            summary,
            account_name=account_name,
            topic_type=topic_type,
            language_code=language_code,
            cta_type=cta_type,
            cta_url=cta_url,
            image_url=image_url,
        )

    @mcp.tool()
    def upload_image_to_drive(
        file_name: str,
        file_base64: str,
        mime_type: str,
        folder_id: str = "root",
        make_public: bool = True,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Upload an image to Drive (base64) and return a public URL for GBP posts."""
        return tools.upload_image_to_drive(
            auth.resolve_credentials(access_token),
            file_name,
            file_base64,
            mime_type,
            folder_id=folder_id,
            make_public=make_public,
        )

    @mcp.tool()
    def reply_to_review(
        review_name: str,
        comment: str,
        location_id: str | None = None,
        account_name: str | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Post a reply to a review. review_name is the v4 review resource name or review id."""
        return tools.reply_to_review(
            auth.resolve_credentials(access_token),
            review_name,
            comment,
            location_id=location_id,
            account_name=account_name,
        )

    @mcp.tool()
    def start_oauth(redirect_uri: str | None = None) -> dict[str, Any]:
        """Return a Google OAuth URL. After approval, call complete_oauth with the code."""
        return auth.start_oauth(redirect_uri)

    @mcp.tool()
    def complete_oauth(code: str, redirect_uri: str | None = None) -> dict[str, Any]:
        """Exchange an OAuth code and store credentials. Does not return tokens."""
        return auth.complete_oauth(code, redirect_uri)

    return mcp


mcp = create_mcp()


def registered_tool_names(server=None):
    """Inspect tools registered on a FastMCP / MCPServer instance."""
    target = server if server is not None else mcp
    manager = getattr(target, "_tool_manager", None)
    if manager is not None:
        stored = getattr(manager, "_tools", None)
        if isinstance(stored, dict):
            return list(stored.keys())
        listed = manager.list_tools()
        return [_tool_name(item) for item in listed]
    list_fn = getattr(target, "list_tools", None)
    if callable(list_fn):
        listed = list_fn()
        if hasattr(listed, "__await__"):
            raise RuntimeError("Use registered_tool_names on a sync tool manager.")
        return [_tool_name(item) for item in listed]
    raise RuntimeError("Cannot inspect MCP tool registry for this SDK version.")


def _tool_name(item):
    if isinstance(item, str):
        return item
    name = getattr(item, "name", None)
    if name:
        return name
    if isinstance(item, dict):
        return item.get("name")
    return str(item)


def _run_http(server, host, port):
    kwargs = {
        "transport": "streamable-http",
        "host": host,
        "port": port,
    }
    try:
        server.run(json_response=True, max_request_body_size=HTTP_MAX_BODY_BYTES, **kwargs)
        return
    except TypeError:
        pass
    try:
        server.run(stateless_http=True, json_response=True, **kwargs)
        return
    except TypeError:
        pass
    server.run(**kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Google Business Profile MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Serve Streamable HTTP instead of stdio.",
    )
    parser.add_argument("--host", default=os.getenv("MCP_HTTP_HOST", DEFAULT_HTTP_HOST))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_HTTP_PORT", str(DEFAULT_HTTP_PORT))),
    )
    parser.add_argument(
        "--oauth",
        action="store_true",
        help="Run the local OAuth helper and exit (does not print tokens).",
    )
    args = parser.parse_args(argv)

    if args.oauth:
        return auth.run_oauth_cli()

    transport = os.getenv("MCP_TRANSPORT", "").strip().lower()
    use_http = args.http or transport in {"http", "streamable-http", "streamable_http"}
    if use_http:
        _run_http(mcp, args.host, args.port)
        return 0

    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
