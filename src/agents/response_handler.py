"""
Response Handler agent for processing Analysis Agent output.
"""

from typing import Any, Dict

from strands import Agent

from utilities.logger import get_logger
from utilities.strands_model import model

logger = get_logger(__name__)


class ResponseHandlerAgent:
    """Agent responsible for processing and formatting Analysis Agent output."""

    def __init__(self):
        self.agent = None
        self._setup_agent()

    def _setup_agent(self) -> None:
        """Set up the Strands agent with configuration."""
        self.agent = Agent(
            name="Response Handler Agent",
            description="Processes and formats Analysis Agent output for frontline response teams.",
            model=model,
            tools=[],
            callback_handler=None,
        )

        logger.info("Response Handler Agent initialized")

    async def process_analysis_output(self, analysis_output: str, alarm_message: str) -> Dict[str, Any]:
        logger.info("Processing Analysis Agent output")

        try:
            # Create response processing prompt
            prompt = self._create_response_prompt(analysis_output, alarm_message)

            # Run the agent
            response = self.agent(prompt)

            return {
                "alarm_message": alarm_message,
                "analysis_output": analysis_output,
                "processed_response": str(response),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Response processing failed: {e}")
            return {
                "alarm_message": alarm_message,
                "analysis_output": analysis_output,
                "error": str(e),
                "status": "error"
            }

    def _create_response_prompt(self, analysis_output: str, alarm_message: str) -> str:
        """Create the response processing prompt for the agent."""
        return f"""
You are the **Response Handler Agent**, responsible for processing Analysis Agent output and preparing it for frontline response teams.

## Your Mission
Take the Analysis Agent's output and format it into clear, actionable guidance for frontline response teams.

## Guidelines
1. Extract the most critical information from the analysis
2. Present immediate actions in a clear, prioritized list
3. Highlight any escalation requirements
4. Provide clear next steps
5. Format the response for quick consumption during incident response
6. Focus on actionable items rather than technical details
7. Ensure the response is concise but comprehensive

## Input Information
**Original Alarm:** {alarm_message}

**Analysis Agent Output:**
{analysis_output}

## Your Task
Process this analysis and provide a clear, actionable response formatted for frontline response teams. Focus on:
- Immediate actions to take
- Escalation procedures if needed
- Key information for incident response
- Clear next steps

Format your response in a structured way that's easy to follow during an incident.
        """.strip()