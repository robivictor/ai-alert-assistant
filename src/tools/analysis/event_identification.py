"""Tool for identifying event IDs from alarm messages."""

from typing import Any, Dict
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


@tool(description="Identify the event ID that best matches the alarm message")
def identify_event_id(alarm_message: str, documentation: Dict[str, Any]) -> str:
    """
    Identify the event ID that best matches the alarm message.

    Args:
        alarm_message: The system alert message
        documentation: Previously found documentation

    Returns:
        Event ID string (e.g., "DB-001")
    """
    logger.info("Identifying event ID for alert")

    # Pattern matching logic for general alerts
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