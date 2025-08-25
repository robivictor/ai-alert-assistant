"""
Main entry point for the AI DBA Assistant.
"""

import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from .agents.analysis import DatabaseAnalysisAgent
from .tools.mcp_client import AtlassianMCPClient
from .utilities.logger import get_logger, log_error, log_success, styled_log
from .utilities.strands_model import get_model_info

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class AIDBAAssistant:
    """Main application class for the AI DBA Assistant."""

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
            self.analysis_agent = DatabaseAnalysisAgent(self.atlassian_client)

            logger.info("AI DBA Assistant initialized successfully")

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

    async def analyze_alarm(self, alarm_message: str) -> dict:
        """
        Analyze a database alarm message.

        Args:
            alarm_message: The alarm message to analyze

        Returns:
            dict: Analysis results and recommendations
        """
        if not self.analysis_agent:
            log_error("Analysis agent not initialized")
            return {"error": "Analysis agent not available", "status": "error"}

        return await self.analysis_agent.analyze_alarm(alarm_message)

    async def interactive_mode(self) -> None:
        """Run the application in interactive mode."""
        styled_log("🤖 AI DBA ASSISTANT", "Interactive mode started", "green")

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

        styled_log("📚 READY", "AI DBA Assistant is ready to analyze alarms", "green")

        while True:
            try:
                # Get user input
                print()  # Add some spacing
                alarm_message = input(
                    "What is the alarm message you want to analyze? (or 'quit' to exit): "
                ).strip()

                if alarm_message.lower() in ["quit", "exit", "q"]:
                    styled_log("👋 GOODBYE", "AI DBA Assistant session ended", "yellow")
                    break

                if not alarm_message:
                    print("Please enter an alarm message.")
                    continue

                # Analyze the alarm
                styled_log("🔍 ANALYZING", "Processing alarm message...", "cyan")
                result = await self.analyze_alarm(alarm_message)

                if result["status"] == "success":
                    print()  # Add spacing
                    styled_log("✅ ANALYSIS COMPLETE", "Results:", "green")
                    print(result["analysis_response"])
                else:
                    log_error(
                        f"Analysis failed: {result.get('error', 'Unknown error')}"
                    )

            except KeyboardInterrupt:
                styled_log("👋 GOODBYE", "AI DBA Assistant session ended", "yellow")
                break
            except Exception as e:
                log_error(f"Error in interactive mode: {e}")
                continue

    async def batch_mode(self, alarm_message: str) -> None:
        """
        Run the application in batch mode with a single alarm.

        Args:
            alarm_message: The alarm message to analyze
        """
        styled_log("🤖 AI DBA ASSISTANT", "Batch mode started", "green")

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

        # Analyze the alarm
        styled_log("🔍 ANALYZING", f"Processing: {alarm_message}", "cyan")
        result = await self.analyze_alarm(alarm_message)

        if result["status"] == "success":
            print()
            styled_log("✅ ANALYSIS COMPLETE", "Results:", "green")
            print(result["analysis_response"])
        else:
            log_error(f"Analysis failed: {result.get('error', 'Unknown error')}")


async def main(alarm_message: Optional[str] = None) -> None:
    """
    Main application entry point.

    Args:
        alarm_message: Optional alarm message for batch mode
    """
    try:
        # Clear terminal
        os.system("clear" if os.name == "posix" else "cls")

        # Create application instance
        app = AIDBAAssistant()

        # Run in appropriate mode
        if alarm_message:
            await app.batch_mode(alarm_message)
        else:
            await app.interactive_mode()

    except Exception as e:
        log_error(f"Application error: {e}")
        sys.exit(1)


def cli() -> None:
    """Command line interface entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI DBA Assistant - Database Alarm Analysis"
    )
    parser.add_argument(
        "alarm",
        nargs="?",
        help="Alarm message to analyze (if not provided, starts interactive mode)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level",
    )

    args = parser.parse_args()

    # Set up logging with specified level
    from .utilities.logger import setup_logging

    setup_logging(args.log_level)

    # Run the application
    asyncio.run(main(args.alarm))


if __name__ == "__main__":
    cli()
