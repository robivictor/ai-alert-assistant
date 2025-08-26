"""
Email tool manager with mock implementation.
"""

from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


class EmailToolManager:
    """Mock email tool manager that prints to console."""

    def __init__(self):
        logger.info("Email Tool Manager initialized (mock)")

    @tool
    def email_customer(self, recipient: str, subject: str, body: str) -> str:
        print("=" * 60)
        print("SENDING EMAIL")
        print("=" * 60)
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60)
        print("Email sent successfully (mock)")
        print()

        logger.info(f"Mock email sent to {recipient}")
        return f"Email sent successfully to {recipient}"