"""Factory for creating analysis tools with MCP manager access."""

import asyncio
from typing import Any, Dict, List
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


def create_analysis_tools(mcp_manager):
    
    @tool(description="Search Confluence documentation for information related to the alarm message")
    def search_alarm_documentation(alarm_message: str) -> Dict[str, Any]:
        logger.info(f"Searching documentation for alert: {alarm_message}")
        keywords = _extract_keywords(alarm_message)
        try:
            search_query = " ".join(keywords)
            search_result = asyncio.run(
                mcp_manager.search_confluence_content(search_query)
            )
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

    @tool(description="Identify the event ID that best matches the alarm message")
    def identify_event_id(alarm_message: str, documentation: Dict[str, Any]) -> str:
        logger.info("Identifying event ID for alert")
        alarm_lower = alarm_message.lower()

        if "cpu" in alarm_lower and (
            "high" in alarm_lower or "90" in alarm_lower or "95" in alarm_lower
        ):
            return "SYS-001"
        elif "memory" in alarm_lower and (
            "critical" in alarm_lower or "exhausted" in alarm_lower
        ):
            return "SYS-002"
        elif "connection" in alarm_lower and (
            "limit" in alarm_lower or "maximum" in alarm_lower
        ):
            return "NET-001"
        elif "disk" in alarm_lower and (
            "space" in alarm_lower or "full" in alarm_lower
        ):
            return "STO-001"
        elif ("service" in alarm_lower or "application" in alarm_lower) and (
            "down" in alarm_lower or "failed" in alarm_lower or "unavailable" in alarm_lower
        ):
            return "APP-001"
        elif "authentication" in alarm_lower or "login" in alarm_lower:
            return "AUTH-001"
        elif "network" in alarm_lower or "timeout" in alarm_lower:
            return "NET-002"
        else:
            return "ALERT-UNKNOWN"

    @tool(description="Get specific troubleshooting steps for the identified event ID")
    def get_troubleshooting_steps(event_id: str) -> Dict[str, Any]:
        logger.info(f"Getting troubleshooting steps for event {event_id}")
        troubleshooting_steps = _get_predefined_steps(event_id)

        return troubleshooting_steps

    @tool(description="Discover available Confluence spaces and pages")
    def get_accessible_atlassian_resources() -> Dict[str, Any]:
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

    @tool(description="Search Confluence content for pages related to the alarm")
    def search_content(query: str, space_key: str = None) -> Dict[str, Any]:
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

    @tool(description="Retrieve detailed content from a specific Confluence page")
    def get_confluence_page(page_id: str) -> Dict[str, Any]:
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

    return [
        search_alarm_documentation,
        identify_event_id,
        get_troubleshooting_steps,
        get_accessible_atlassian_resources,
        search_content,
        get_confluence_page,
    ]


def _extract_keywords(alarm_message: str) -> List[str]:
    keywords = []
    alarm_lower = alarm_message.lower()
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

    import re
    numbers = re.findall(r"\d+%?", alarm_message)
    keywords.extend(numbers)

    return keywords


def _get_predefined_steps(event_id: str) -> Dict[str, Any]:
    alert_steps = {
        "SYS-001": {
            "event_name": "High CPU Usage",
            "immediate_actions": [
                "Check top processes consuming CPU",
                "Review system load averages",
                "Identify resource-intensive applications",
                "Consider scaling or load balancing",
            ],
            "escalation": "If CPU remains high for >15 minutes, page on-call engineer",
            "severity": "Critical",
        },
        "SYS-002": {
            "event_name": "Memory Pressure",
            "immediate_actions": [
                "Review memory usage by processes",
                "Check for memory leaks in applications",
                "Clear unnecessary caches",
                "Monitor swap usage and consider restart",
            ],
            "escalation": "Critical - immediate system admin involvement required",
            "severity": "Critical",
        },
        "NET-001": {
            "event_name": "Connection Limit Reached",
            "immediate_actions": [
                "Review active connections",
                "Check for connection leaks in applications",
                "Increase connection limits if appropriate",
                "Monitor connection pool usage",
            ],
            "escalation": "If connections don't decrease within 10 minutes",
            "severity": "Critical",
        },
        "STO-001": {
            "event_name": "Disk Space Low",
            "immediate_actions": [
                "Identify largest files and directories",
                "Clean up temporary files and logs",
                "Archive old data if possible",
                "Consider adding storage capacity",
            ],
            "escalation": "If disk usage >95%, immediate action required",
            "severity": "High",
        },
        "APP-001": {
            "event_name": "Service/Application Down",
            "immediate_actions": [
                "Check service status and logs",
                "Attempt service restart",
                "Verify dependencies are running",
                "Check for recent deployments or changes",
            ],
            "escalation": "If service doesn't recover in 5 minutes, escalate",
            "severity": "Critical",
        },
        "AUTH-001": {
            "event_name": "Authentication Issues",
            "immediate_actions": [
                "Check authentication service status",
                "Review authentication logs",
                "Verify user credentials and permissions",
                "Check network connectivity to auth services",
            ],
            "escalation": "If affecting multiple users, escalate immediately",
            "severity": "High",
        },
        "NET-002": {
            "event_name": "Network/Timeout Issues",
            "immediate_actions": [
                "Check network connectivity",
                "Review firewall and routing rules",
                "Test DNS resolution",
                "Monitor network latency and packet loss",
            ],
            "escalation": "If affecting multiple services, escalate",
            "severity": "High",
        },
    }

    return alert_steps.get(
        event_id,
        {
            "event_name": "Unknown Event",
            "immediate_actions": ["Review alarm details", "Check system logs"],
            "escalation": "Contact system admin team for analysis",
            "severity": "Unknown",
        },
    )