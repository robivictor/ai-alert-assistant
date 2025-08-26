"""
Core application class for the AI Alert Assistant.
"""

import asyncio
import os
from typing import Optional

from agents.analysis import AlertAnalysisAgent
from agents.frontline_response import FrontlineResponseAgent
from tools.mcp_client import AtlassianMCPClient
from utilities.logger import get_logger, log_error, log_success, styled_log
from utilities.strands_model import get_model_info

logger = get_logger(__name__)


class AIAlertAssistant:
    """Main application class for the AI Alert Assistant."""

    def __init__(self):
        self.atlassian_client = None
        self.analysis_agent = None
        self.frontline_response = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the application components."""
        try:
            # Initialize MCP client
            confluence_url = os.getenv("CONFLUENCE_URL")
            self.atlassian_client = AtlassianMCPClient(confluence_url)

            # Initialize analysis agent
            self.analysis_agent = AlertAnalysisAgent(self.atlassian_client)
            
            # Initialize frontline response agent
            self.frontline_response = FrontlineResponseAgent()

            logger.info("AI Alert Assistant initialized successfully")

        except Exception as e:
            log_error(f"Failed to initialize application: {e}")
            raise

    async def authenticate(self) -> bool:
        """Validate MCP client configuration."""
        styled_log(
            "🔐 CONFIGURATION", "Validating MCP client configuration...", "yellow"
        )

        try:
            success = await self.atlassian_client.validate_configuration()
            if success:
                log_success("MCP client configuration valid")
                return True
            else:
                log_error("MCP client configuration failed")
                return False

        except Exception as e:
            log_error(f"Configuration error: {e}")
            return False

    async def analyze_alert(self, alert_message: str) -> dict:
        if not self.analysis_agent:
            log_error("Analysis agent not initialized")
            return {"error": "Analysis agent not available", "status": "error"}
            
        if not self.frontline_response:
            log_error("Frontline response agent not initialized")
            return {"error": "Frontline response agent not available", "status": "error"}

        # Step 1: Get analysis from Analysis Agent
        analysis_result = await self.analysis_agent.analyze_alert(alert_message)
        
        if analysis_result["status"] != "success":
            return analysis_result
            
        # Step 2: Take action with Frontline Response Agent
        response_result = await self.frontline_response.take_action(
            alert_message,
            analysis_result["analysis_response"]
        )
        
        if response_result["status"] == "success":
            return {
                "alert_message": alert_message,
                "analysis_response": response_result["response"],
                "status": "success"
            }
        else:
            # Fallback to original analysis if frontline response fails
            return analysis_result

    def show_startup_info(self) -> None:
        """Display startup information."""
        styled_log("🤖 AI ALERT ASSISTANT", "Starting up...", "green")

        # Show model information
        model_info = get_model_info()
        styled_log(
            "MODEL INFO",
            f"Using {model_info['provider']} - {model_info['model_name']}",
            "cyan",
        )