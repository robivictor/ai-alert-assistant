"""
Command line interface handler for the AI Alert Assistant.
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from core.application import AIAlertAssistant
from utilities.logger import log_error, setup_logging

# Load environment variables
load_dotenv()


async def process_alert(alert_message: str) -> None:
    app = AIAlertAssistant()

    if not await app.authenticate():
        return

    result = await app.analyze_alert(alert_message)

    if result["status"] == "success":
        print(result["analysis_response"])
    else:
        log_error(f"Analysis failed: {result.get('error', 'Unknown error')}")


def parse_args() -> str:
    """Parse command line arguments and return alert message."""
    parser = argparse.ArgumentParser(description="AI Alert Assistant - System Alert Analysis")
    parser.add_argument("alert", help="Alert message to analyze")
    args = parser.parse_args()
    return args.alert


def main() -> None:
    """Main entry point."""
    alert_message = parse_args()
    setup_logging()
    asyncio.run(process_alert(alert_message))