"""Tool for getting troubleshooting steps for event IDs."""

from typing import Any, Dict
from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


@tool(description="Get specific troubleshooting steps for the identified event ID")
def get_troubleshooting_steps(event_id: str) -> Dict[str, Any]:
    logger.info(f"Getting troubleshooting steps for event {event_id}")
    troubleshooting_steps = _get_predefined_steps(event_id)

    return troubleshooting_steps


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