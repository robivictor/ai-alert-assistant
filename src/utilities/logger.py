"""
Logging configuration for AI DBA Assistant.
"""

import logging
import os
import sys
from typing import Optional

from termcolor import colored


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    COLORS = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "magenta",
    }

    def format(self, record):
        """Format the log record with colors."""
        log_message = super().format(record)

        # Add color based on log level
        color = self.COLORS.get(record.levelname, "white")

        # Format: [LEVEL] module_name: message
        colored_level = colored(f"[{record.levelname}]", color, attrs=["bold"])
        colored_name = colored(record.name, "blue")

        return f"{colored_level} {colored_name}: {record.getMessage()}"


def setup_logging(level: str = None) -> None:
    """
    Set up logging configuration for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get log level from environment or parameter
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Set formatter
    formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def styled_log(header: str, message: str, color: str = "white") -> None:
    """
    Log a styled message with colored header.

    Args:
        header: Header text (will be colored and bolded)
        message: Message content
        color: Color for the header
    """
    logger = get_logger("ai_dba.styled")
    colored_header = colored(f"{header}:", color, attrs=["bold"])
    colored_message = colored(message, color)
    print(f"{colored_header}\n{colored_message}")


def log_tool_call(tool_name: str, message: str) -> None:
    """
    Log a tool call with consistent formatting.

    Args:
        tool_name: Name of the tool being called
        message: Message about the tool call
    """
    styled_log(f" {tool_name}", message, "magenta")


def log_error(message: str) -> None:
    """
    Log an error message with consistent formatting.

    Args:
        message: Error message
    """
    styled_log("ERROR", message, "red")


def log_success(message: str) -> None:
    """
    Log a success message with consistent formatting.

    Args:
        message: Success message
    """
    styled_log("SUCCESS", message, "green")


def log_warning(message: str) -> None:
    """
    Log a warning message with consistent formatting.

    Args:
        message: Warning message
    """
    styled_log("WARNING", message, "yellow")


# Initialize logging on module import
setup_logging()

# Export commonly used functions
__all__ = [
    "setup_logging",
    "get_logger",
    "styled_log",
    "log_tool_call",
    "log_error",
    "log_success",
    "log_warning",
]
