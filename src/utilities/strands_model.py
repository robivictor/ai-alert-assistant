"""
Strands model configuration and management.
"""

import os
from typing import Union

from dotenv import load_dotenv
from strands.models.ollama import OllamaModel
from strands.models.openai import OpenAIModel

from .logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class ModelConfig:
    """Configuration class for AI models."""

    def __init__(self):
        self.model_type = os.getenv("MODEL_TYPE", "openai").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        self.ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def validate(self) -> None:
        """Validate the model configuration."""
        if self.model_type == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI models. "
                "Please set it in your .env file or environment."
            )

        if self.model_type not in ["openai", "ollama"]:
            raise ValueError(
                f"Unsupported model type: {self.model_type}. "
                "Supported types: openai, ollama"
            )


def create_model() -> Union[OpenAIModel, OllamaModel]:
    """
    Create and return the appropriate AI model based on configuration.

    Returns:
        Union[OpenAIModel, OllamaModel]: Configured model instance

    Raises:
        ValueError: If configuration is invalid or required keys are missing
    """
    config = ModelConfig()
    config.validate()

    if config.model_type == "openai":
        logger.info(f"Creating OpenAI model: {config.openai_model}")
        return OpenAIModel(model_id=config.openai_model, api_key=config.openai_api_key)

    elif config.model_type == "ollama":
        logger.info(
            f"Creating Ollama model: {config.ollama_model} at {config.ollama_host}"
        )
        return OllamaModel(model=config.ollama_model, host=config.ollama_host)

    else:
        # This shouldn't happen due to validation, but just in case
        raise ValueError(f"Unsupported model type: {config.model_type}")


def get_model_info() -> dict:
    """
    Get information about the current model configuration.

    Returns:
        dict: Model configuration information
    """
    config = ModelConfig()

    info = {"model_type": config.model_type, "configured": True}

    if config.model_type == "openai":
        info.update(
            {
                "model_name": config.openai_model,
                "api_key_configured": bool(config.openai_api_key),
                "provider": "OpenAI",
            }
        )
    elif config.model_type == "ollama":
        info.update(
            {
                "model_name": config.ollama_model,
                "host": config.ollama_host,
                "provider": "Ollama",
            }
        )

    return info


# Create the default model instance
try:
    model = create_model()
    logger.info("Model created successfully")
except Exception as e:
    logger.error(f"Failed to create model: {e}")
    # Don't raise here to allow for graceful degradation
    model = None


# Export the model instance and factory functions
__all__ = ["model", "create_model", "get_model_info", "ModelConfig"]
