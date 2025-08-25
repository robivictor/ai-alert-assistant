"""
Analysis agent for database alarm processing.
"""

import asyncio
from typing import Any, Dict, List

from strands import Agent
from strands.tools import tool

from ..tools.mcp_client import AtlassianMCPClient, MCPToolManager
from ..utilities.logger import get_logger, styled_log
from ..utilities.strands_model import model

logger = get_logger(__name__)


class DatabaseAnalysisAgent:
    """Agent responsible for analyzing database alarms using Confluence documentation."""

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
            name="Database Analysis Agent",
            description="Analyzes database alarms and provides troubleshooting guidance based on Confluence documentation.",
            model=model,
            tools=custom_tools,
            callback_handler=None,
        )

        logger.info("Database Analysis Agent initialized")

    @tool
    def search_alarm_documentation(self, alarm_message: str) -> Dict[str, Any]:
        """
        Search Confluence documentation for information related to the alarm message.

        Args:
            alarm_message: The database alarm message to analyze

        Returns:
            Dict containing search results and relevant documentation
        """
        logger.info(f"Searching documentation for alarm: {alarm_message}")

        # Extract keywords from alarm message for search
        keywords = self._extract_keywords(alarm_message)

        # Use mcp-atlassian to search for documentation
        try:
            search_query = " ".join(keywords)
            search_result = asyncio.run(
                self.mcp_manager.search_confluence_content(search_query)
            )

            return {
                "alarm_message": alarm_message,
                "keywords": keywords,
                "search_performed": True,
                "search_results": search_result,
                "documentation_found": search_result.get("status") == "success",
            }
        except Exception as e:
            logger.error(f"Documentation search failed: {e}")
            return {
                "alarm_message": alarm_message,
                "keywords": keywords,
                "search_performed": False,
                "error": str(e),
                "documentation_found": False,
            }

    @tool
    def identify_event_id(
        self, alarm_message: str, documentation: Dict[str, Any]
    ) -> str:
        """
        Identify the event ID that best matches the alarm message.

        Args:
            alarm_message: The database alarm message
            documentation: Previously found documentation

        Returns:
            Event ID string (e.g., "DB-001")
        """
        logger.info("Identifying event ID for alarm")

        # Pattern matching logic
        alarm_lower = alarm_message.lower()

        if "cpu" in alarm_lower and (
            "high" in alarm_lower or "90" in alarm_lower or "95" in alarm_lower
        ):
            return "DB-001"
        elif "memory" in alarm_lower and (
            "critical" in alarm_lower or "exhausted" in alarm_lower
        ):
            return "DB-002"
        elif "connection" in alarm_lower and (
            "limit" in alarm_lower or "maximum" in alarm_lower
        ):
            return "DB-003"
        elif "disk" in alarm_lower and (
            "space" in alarm_lower or "full" in alarm_lower
        ):
            return "DB-004"
        elif "replication" in alarm_lower and (
            "lag" in alarm_lower or "delay" in alarm_lower
        ):
            return "DB-005"
        elif "deadlock" in alarm_lower:
            return "DB-006"
        elif "backup" in alarm_lower and "fail" in alarm_lower:
            return "DB-007"
        else:
            return "DB-UNKNOWN"

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
        """Extract relevant keywords from alarm message."""
        keywords = []
        alarm_lower = alarm_message.lower()

        # Database-related keywords
        db_keywords = [
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
        ]

        for keyword in db_keywords:
            if keyword in alarm_lower:
                keywords.append(keyword)

        # Extract numeric values that might indicate thresholds
        import re

        numbers = re.findall(r"\d+%?", alarm_message)
        keywords.extend(numbers)

        return keywords

    def _get_predefined_steps(self, event_id: str) -> Dict[str, Any]:
        """Get predefined troubleshooting steps for event ID."""
        steps_db = {
            "DB-001": {
                "event_name": "High CPU Usage",
                "immediate_actions": [
                    "Check current running queries",
                    "Identify long-running transactions",
                    "Review connection pool usage",
                    "Check for blocking locks",
                ],
                "escalation": "If CPU remains high for >15 minutes, page on-call DBA",
                "severity": "Critical",
            },
            "DB-002": {
                "event_name": "Memory Pressure",
                "immediate_actions": [
                    "Review memory allocation settings",
                    "Check for memory leaks in applications",
                    "Restart non-critical database connections",
                    "Monitor swap usage",
                ],
                "escalation": "Critical - immediate DBA involvement required",
                "severity": "Critical",
            },
            "DB-003": {
                "event_name": "Connection Limit Reached",
                "immediate_actions": [
                    "Kill idle connections older than 30 minutes",
                    "Review application connection pooling",
                    "Increase max_connections temporarily if safe",
                    "Check for connection leaks",
                ],
                "escalation": "If connections don't decrease within 10 minutes",
                "severity": "Critical",
            },
        }

        return steps_db.get(
            event_id,
            {
                "event_name": "Unknown Event",
                "immediate_actions": ["Review alarm details", "Check system logs"],
                "escalation": "Contact DBA team for analysis",
                "severity": "Unknown",
            },
        )

    async def analyze_alarm(self, alarm_message: str) -> Dict[str, Any]:
        """
        Main method to analyze a database alarm.

        Args:
            alarm_message: The alarm message to analyze

        Returns:
            Dict containing analysis results and recommendations
        """
        logger.info(f"Starting alarm analysis: {alarm_message}")
        styled_log("ALARM", alarm_message, "yellow")

        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(alarm_message)

            # Run the agent analysis
            response = self.agent(prompt)

            styled_log(" ANALYSIS_BOT", str(response), "blue")

            return {
                "alarm_message": alarm_message,
                "analysis_response": str(response),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"alarm_message": alarm_message, "error": str(e), "status": "error"}

    def _create_analysis_prompt(self, alarm_message: str) -> str:
        """Create the analysis prompt for the agent."""
        return f"""
You are the Database Analysis Agent, responsible for analyzing database alarms and providing troubleshooting guidance.

## Your Mission
Analyze the following database alarm and provide structured, actionable recommendations based on available documentation.

## Available Tools
1. search_alarm_documentation - Search Confluence for relevant documentation
2. identify_event_id - Map the alarm to a specific event ID
3. get_troubleshooting_steps - Get detailed troubleshooting procedures
4. MCP Confluence tools - Access live documentation

## Process
1. Use search_alarm_documentation to find relevant information
2. Use identify_event_id to classify the alarm
3. Use get_troubleshooting_steps to get specific procedures  
4. Use MCP tools to access live Confluence documentation if available
5. Provide a comprehensive response with:
   - Event ID classification
   - Immediate actions to take
   - Escalation procedures
   - Links to relevant documentation

## Alarm to Analyze
{alarm_message}

Please analyze this alarm systematically and provide clear, actionable guidance.
        """.strip()
