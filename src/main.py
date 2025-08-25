"""
Main entry point for the AI Alert Assistant.
"""

import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from agents.analysis import AlertAnalysisAgent
from tools.mcp_client import AtlassianMCPClient
from utilities.logger import get_logger, log_error, log_success, styled_log
from utilities.strands_model import get_model_info

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class AIAlertAssistant:
    """Main application class for the AI Alert Assistant."""

    def __init__(self):
        self.atlassian_client = None
        self.analysis_agent = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the application components."""
        try:
            # Initialize MCP client
            confluence_url = os.getenv("CONFLUENCE_URL")
            self.atlassian_client = AtlassianMCPClient(confluence_url)

            # Initialize analysis agent
            self.analysis_agent = AlertAnalysisAgent(self.atlassian_client)

            logger.info("AI Alert Assistant initialized successfully")

        except Exception as e:
            log_error(f"Failed to initialize application: {e}")
            raise

    async def authenticate(self) -> bool:
        """Authenticate with Atlassian services."""
        styled_log(
            "🔐 AUTHENTICATION", "Starting Atlassian authentication...", "yellow"
        )

        try:
            success = await self.atlassian_client.authenticate()
            if success:
                log_success("Atlassian authentication successful")
                return True
            else:
                log_error("Atlassian authentication failed")
                return False

        except Exception as e:
            log_error(f"Authentication error: {e}")
            return False

    async def analyze_alert(self, alert_message: str) -> dict:
        """
        Analyze a system alert message.

        Args:
            alert_message: The alert message to analyze

        Returns:
            dict: Analysis results and recommendations
        """
        if not self.analysis_agent:
            log_error("Analysis agent not initialized")
            return {"error": "Analysis agent not available", "status": "error"}

        return await self.analysis_agent.analyze_alert(alert_message)

    async def interactive_mode(self) -> None:
        """Run the application in interactive mode."""
        styled_log("🤖 AI ALERT ASSISTANT", "Interactive mode started", "green")

        # Show model information
        model_info = get_model_info()
        styled_log(
            "MODEL INFO",
            f"Using {model_info['provider']} - {model_info['model_name']}",
            "cyan",
        )

        # Authenticate
        if not await self.authenticate():
            log_error("Authentication required to continue")
            return

        styled_log("📚 READY", "AI Alert Assistant is ready to analyze alerts", "green")

        while True:
            try:
                # Get user input
                print()  # Add some spacing
                alert_message = input(
                    "What is the alert message you want to analyze? (or 'quit' to exit): "
                ).strip()

                if alert_message.lower() in ["quit", "exit", "q"]:
                    styled_log("👋 GOODBYE", "AI Alert Assistant session ended", "yellow")
                    break

                if not alert_message:
                    print("Please enter an alert message.")
                    continue

                # Analyze the alert
                styled_log("🔍 ANALYZING", "Processing alert message...", "cyan")
                result = await self.analyze_alert(alert_message)

                if result["status"] == "success":
                    print()  # Add spacing
                    styled_log("✅ ANALYSIS COMPLETE", "Results:", "green")
                    print(result["analysis_response"])
                else:
                    log_error(
                        f"Analysis failed: {result.get('error', 'Unknown error')}"
                    )

            except KeyboardInterrupt:
                styled_log("👋 GOODBYE", "AI Alert Assistant session ended", "yellow")
                break
            except Exception as e:
                log_error(f"Error in interactive mode: {e}")
                continue

    async def batch_mode(self, alert_message: str) -> None:
        """
        Run the application in batch mode with a single alert.

        Args:
            alert_message: The alert message to analyze
        """
        styled_log("🤖 AI ALERT ASSISTANT", "Batch mode started", "green")

        # Show model information
        model_info = get_model_info()
        styled_log(
            "MODEL INFO",
            f"Using {model_info['provider']} - {model_info['model_name']}",
            "cyan",
        )

        # Authenticate
        if not await self.authenticate():
            log_error("Authentication required to continue")
            return

        # Analyze the alert
        styled_log("🔍 ANALYZING", f"Processing: {alert_message}", "cyan")
        result = await self.analyze_alert(alert_message)

        if result["status"] == "success":
            print()
            styled_log("✅ ANALYSIS COMPLETE", "Results:", "green")
            print(result["analysis_response"])
        else:
            log_error(f"Analysis failed: {result.get('error', 'Unknown error')}")


async def main(alert_message: Optional[str] = None) -> None:
    """
    Main application entry point.

    Args:
        alert_message: Optional alert message for batch mode
    """
    try:
        # Clear terminal
        os.system("clear" if os.name == "posix" else "cls")

        # Create application instance
        app = AIAlertAssistant()

        # Run in appropriate mode
        if alert_message:
            await app.batch_mode(alert_message)
        else:
            await app.interactive_mode()

    except Exception as e:
        log_error(f"Application error: {e}")
        sys.exit(1)


def cli() -> None:
    """Command line interface entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Alert Assistant - System Alert Analysis"
    )
    parser.add_argument(
        "alert",
        nargs="?",
        help="Alert message to analyze (if not provided, starts interactive mode)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level",
    )

    args = parser.parse_args()

    # Set up logging with specified level
    from utilities.logger import setup_logging

    setup_logging(args.log_level)

    # Run the application
    asyncio.run(main(args.alert))


if __name__ == "__main__":
    cli()
