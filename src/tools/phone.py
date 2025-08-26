"""
Phone tool manager with mock implementation.
"""

from strands.tools import tool
from utilities.logger import get_logger

logger = get_logger(__name__)


class PhoneToolManager:
    """Mock phone tool manager that prints to console."""

    def __init__(self):
        logger.info("Phone Tool Manager initialized (mock)")

    @tool
    def call_customer(self, phone_number: str, message: str) -> str:
        print("=" * 60)
        print("CALLING CUSTOMER")
        print("=" * 60)
        print(f"Calling: {phone_number}")
        print(f"Message: {message}")
        print("=" * 60)
        print("Call completed successfully (mock)")
        print()

        logger.info(f"Mock call made to {phone_number}")
        return f"Call completed successfully to {phone_number}"