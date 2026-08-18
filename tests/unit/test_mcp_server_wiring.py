from src.gmb_mcp.server import TOOL_NAMES, create_mcp, registered_tool_names


def test_expected_tools_are_declared():
    assert "list_accounts" in TOOL_NAMES
    assert "list_locations" in TOOL_NAMES
    assert "get_daily_metrics" in TOOL_NAMES
    assert "get_search_keywords" in TOOL_NAMES
    assert "list_reviews" in TOOL_NAMES
    assert "list_posts" in TOOL_NAMES
    assert "list_media" in TOOL_NAMES
    assert "list_questions" in TOOL_NAMES
    assert "profile_health_check" in TOOL_NAMES
    assert "create_local_post" in TOOL_NAMES
    assert "upload_image_to_drive" in TOOL_NAMES
    assert "reply_to_review" in TOOL_NAMES
    assert "start_oauth" in TOOL_NAMES
    assert "complete_oauth" in TOOL_NAMES


def test_create_mcp_registers_declared_tools():
    server = create_mcp()
    registered = set(registered_tool_names(server))
    missing = set(TOOL_NAMES) - registered
    assert not missing, f"MCP tools not registered: {sorted(missing)}"
