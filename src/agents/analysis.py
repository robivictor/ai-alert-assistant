"""
Analysis agent for general alert processing.
"""

import asyncio
from typing import Any, Dict, List

from strands import Agent

from tools.mcp_client import AtlassianMCPClient, MCPToolManager
from tools.analysis.tool_factory import create_analysis_tools
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
        custom_tools = create_analysis_tools(self.mcp_manager)

        self.agent = Agent(
            name="Analysis Agent",
            description="Analysis Agent supporting the Frontline Response Agent by analyzing alarms and extracting critical details.",
            model=model,
            tools=custom_tools,
            callback_handler=None,
        )

        logger.info("Analysis Agent initialized")

    async def analyze_alert(self, alert_message: str) -> Dict[str, Any]:
        logger.info(f"Starting alert analysis: {alert_message}")
        styled_log("ALERT", alert_message, "yellow")

        try:
            prompt = self._create_analysis_prompt(alert_message)
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

    def _create_analysis_prompt(self, alarm_message: str) -> str:
        return f"""
You are the **Analysis Agent**, supporting the **Frontline Response Agent** by analyzing alarms and extracting critical details.

## Goals
1. Gather any useful information about the alarm message.
2. Find the closest event in the documentation to the alarm message by searching through all available Confluence documentation.
3. Provide a clear event ID and context for the Frontline Response Agent.

## Process
- Step 1: Use your tools to gain understanding on what's happening in the alarm message.
- Step 2: Use getAccessibleAtlassianResources to discover available Confluence spaces and pages.
- Step 3: Use searchContent to find relevant documentation pages related to the alarm.
- Step 4: Use getConfluencePage to retrieve detailed content from relevant pages.
- Step 5: Match the event ID in the documentation to the alarm message. Note that the event ID is almost never mentioned in the alarm message.
- Step 6: Provide frontline response instructions for the Frontline Response Agent, please ignore the DBA response instructions.
- Step 7: Share a link to the email template if found in documentation.

## Objective
Search through ALL available Confluence documentation to find the event ID and useful information for this alarm message: `{alarm_message}`

Start by discovering what Confluence resources are available, then search for content related to the alarm.
        """.strip()
