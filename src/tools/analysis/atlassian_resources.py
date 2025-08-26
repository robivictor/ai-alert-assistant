"""Tool for discovering accessible Atlassian resources."""

import asyncio
from typing import Any, Dict
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


@tool(description="Discover available Confluence spaces and pages")
def get_accessible_atlassian_resources(mcp_manager) -> Dict[str, Any]:
    logger.info("Discovering accessible Atlassian resources")

    try:
        result = asyncio.run(mcp_manager.discover_confluence_resources())
        return result
    except Exception as e:
        logger.warning(f"Failed to discover Atlassian resources: {e}")
        return {
            "status": "error",
            "message": "Unable to discover Confluence resources",
            "error": str(e)
        }