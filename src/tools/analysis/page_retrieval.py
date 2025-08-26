"""Tool for retrieving Confluence pages."""

import asyncio
from typing import Any, Dict
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


@tool(description="Retrieve detailed content from a specific Confluence page")
def get_confluence_page(mcp_manager, page_id: str) -> Dict[str, Any]:
    logger.info(f"Retrieving Confluence page: {page_id}")

    try:
        result = asyncio.run(mcp_manager.get_confluence_page(page_id))
        return result
    except Exception as e:
        logger.warning(f"Failed to retrieve Confluence page: {e}")
        return {
            "status": "error",
            "message": "Unable to retrieve Confluence page",
            "error": str(e),
            "page_id": page_id
        }