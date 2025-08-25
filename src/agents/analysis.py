"""
Analysis agent for general alert processing.
"""

import asyncio
from typing import Any, Dict, List

from strands import Agent
from strands.tools import tool

from tools.mcp_client import AtlassianMCPClient, MCPToolManager
from utilities.logger import get_logger, styled_log
from utilities.strands_model import model

logger = get_logger(__name__)


class AlertAnalysisAgent:
    """Agent responsible for analyzing system alerts using Confluence documentation."""

    def __init__(self, atlassian_client: AtlassianMCPClient):
        self.atlassian_client = atlassian_client
        self.mcp_manager = MCPToolManager(atlassian_client)
        self.agent = None
        self._setup_agent()

    def _setup_agent(self) -> None:
        """Set up the Strands agent with tools and configuration."""
        # Add custom tools (Confluence tools will be added asynchronously)
        custom_tools = [
            self.search_alarm_documentation,
            self.identify_event_id,
            self.get_troubleshooting_steps,
        ]

        self.agent = Agent(
            name="Alert Analysis Agent",
            description="Analyzes system alerts and provides troubleshooting guidance based on Confluence documentation.",
            model=model,
            tools=custom_tools,
            callback_handler=None,
        )

        logger.info("Alert Analysis Agent initialized")

    @tool
    def search_alarm_documentation(self, alarm_message: str) -> Dict[str, Any]:
        """
        Search Confluence documentation for information related to the alarm message.

        Args:
            alarm_message: The system alert message to analyze

        Returns:
            Dict containing search results and relevant documentation
        """
        logger.info(f"Searching documentation for alert: {alarm_message}")

        # Extract keywords from alarm message for search
        keywords = self._extract_keywords(alarm_message)

        # Use mcp-atlassian to search for documentation with graceful fallback
        try:
            search_query = " ".join(keywords)
            search_result = asyncio.run(
                self.mcp_manager.search_confluence_content(search_query)
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

    @tool
    def identify_event_id(
        self, alarm_message: str, documentation: Dict[str, Any]
    ) -> str:
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

    @tool
    def get_troubleshooting_steps(self, event_id: str) -> Dict[str, Any]:
        """
        Get specific troubleshooting steps for the identified event ID.

        Args:
            event_id: The event ID (e.g., "DB-001")

        Returns:
            Dict containing troubleshooting steps and escalation info
        """
        logger.info(f"Getting troubleshooting steps for event {event_id}")

        # This would typically query the actual documentation
        # For now, return predefined steps based on event ID
        troubleshooting_steps = self._get_predefined_steps(event_id)

        return troubleshooting_steps

    def _extract_keywords(self, alarm_message: str) -> List[str]:
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

    def _get_predefined_steps(self, event_id: str) -> Dict[str, Any]:
        """Get predefined troubleshooting steps for event ID."""
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

    async def analyze_alert(self, alert_message: str) -> Dict[str, Any]:
        """
        Main method to analyze a system alert.

        Args:
            alert_message: The alert message to analyze

        Returns:
            Dict containing analysis results and recommendations
        """
        logger.info(f"Starting alert analysis: {alert_message}")
        styled_log("ALERT", alert_message, "yellow")

        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(alert_message)

            # Run the agent analysis
            response = self.agent(prompt)

            styled_log(" ANALYSIS_BOT", str(response), "blue")

            return {
                "alert_message": alert_message,
                "analysis_response": str(response),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"alert_message": alert_message, "error": str(e), "status": "error"}

    def _create_analysis_prompt(self, alert_message: str) -> str:
        """Create the analysis prompt for the agent."""
        return f"""
You are the Alert Analysis Agent, responsible for analyzing system alerts and providing troubleshooting guidance.

## Your Mission
Analyze the following system alert and provide structured, actionable recommendations based on available documentation.

## Available Tools
1. search_alarm_documentation - Search Confluence for relevant documentation
2. identify_event_id - Map the alert to a specific event ID
3. get_troubleshooting_steps - Get detailed troubleshooting procedures
4. MCP Confluence tools - Access live documentation

## Process
1. Use search_alarm_documentation ONCE to find relevant information (do not repeat searches)
2. Use identify_event_id to classify the alert based on the content
3. Use get_troubleshooting_steps to get specific procedures for the identified event ID
4. If documentation search fails, proceed with general analysis based on the alert content
5. Provide a comprehensive response with:
   - Event ID classification
   - Immediate actions to take
   - Escalation procedures
   - General troubleshooting guidance

## Alert to Analyze
{alert_message}

Please analyze this alert systematically and provide clear, actionable guidance.
        """.strip()
