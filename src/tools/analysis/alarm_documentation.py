"""Tool for searching alarm documentation."""

import asyncio
from typing import Any, Dict, List
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


@tool(description="Search Confluence documentation for information related to the alarm message")
def search_alarm_documentation(mcp_manager, alarm_message: str) -> Dict[str, Any]:
    """
    Search Confluence documentation for information related to the alarm message.

    Args:
        mcp_manager: The MCP tool manager instance
        alarm_message: The system alert message to analyze

    Returns:
        Dict containing search results and relevant documentation
    """
    logger.info(f"Searching documentation for alert: {alarm_message}")

    # Extract keywords from alarm message for search
    keywords = _extract_keywords(alarm_message)

    # Use mcp-atlassian to search for documentation with graceful fallback
    try:
        search_query = " ".join(keywords)
        search_result = asyncio.run(
            mcp_manager.search_confluence_content(search_query)
        )

        # Handle both success and partial_success (fallback) cases
        search_performed = search_result.get("status") in ["success", "partial_success"]
        documentation_found = search_result.get("status") == "success"

        return {
            "alarm_message": alarm_message,
            "keywords": keywords,
            "search_performed": search_performed,
            "search_results": search_result,
            "documentation_found": documentation_found,
            "fallback_used": search_result.get("fallback", False),
        }
    except Exception as e:
        logger.warning(f"Documentation search failed, using fallback: {e}")
        return {
            "alarm_message": alarm_message,
            "keywords": keywords,
            "search_performed": False,
            "error": str(e),
            "documentation_found": False,
            "fallback_used": True,
        }


def _extract_keywords(alarm_message: str) -> List[str]:
    """Extract relevant keywords from alert message."""
    keywords = []
    alarm_lower = alarm_message.lower()

    # System alert keywords
    alert_keywords = [
        "cpu",
        "memory",
        "disk",
        "connection",
        "replication",
        "deadlock",
        "backup",
        "performance",
        "query",
        "lock",
        "network",
        "application",
        "service",
        "server",
        "storage",
        "authentication",
        "timeout"
    ]

    for keyword in alert_keywords:
        if keyword in alarm_lower:
            keywords.append(keyword)

    # Extract numeric values that might indicate thresholds
    import re
    numbers = re.findall(r"\d+%?", alarm_message)
    keywords.extend(numbers)

    return keywords