"""Tool for searching Confluence content."""

import asyncio
from typing import Any, Dict
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


@tool(description="Search Confluence content for pages related to the alarm")
def search_content(mcp_manager, query: str, space_key: str = None) -> Dict[str, Any]:
    logger.info(f"Searching Confluence content for: {query}")

    try:
        result = asyncio.run(mcp_manager.search_confluence_content(query, space_key))
        return result
    except Exception as e:
        logger.warning(f"Failed to search Confluence content: {e}")
        return {
            "status": "error",
            "message": "Unable to search Confluence content",
            "error": str(e),
            "query": query
        }