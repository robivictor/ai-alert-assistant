"""
Frontline Response agent for taking appropriate actions based on analysis.
"""

from typing import Any, Dict

from strands import Agent
from tools.email import EmailToolManager
from tools.phone import PhoneToolManager
from utilities.logger import get_logger, styled_log
from utilities.strands_model import model

logger = get_logger(__name__)


class FrontlineResponseAgent:
    """Agent responsible for taking appropriate actions based on analysis output."""

    def __init__(self):
        self.agent = None
        self._setup_agent()

    def _setup_agent(self) -> None:
        """Set up the Strands agent with tools and configuration."""
        # Initialize tool managers
        email_manager = EmailToolManager()
        phone_manager = PhoneToolManager()
        
        self.agent = Agent(
            name="Frontline Response Agent",
            description="Retrieves an analysis and takes appropriate actions.",
            model=model,
            tools=[
                email_manager.email_customer,
                phone_manager.call_customer,
            ],
            callback_handler=None,
        )

        logger.info("Frontline Response Agent initialized with mock tools")

    async def take_action(self, alarm_text: str, analysis: str) -> Dict[str, Any]:
        """
        Take appropriate actions based on the analysis.

        Args:
            alarm_text: Original alarm message
            analysis: Output from the Analysis Agent

        Returns:
            Dict containing response and actions taken
        """
        logger.info("Taking frontline response actions")

        try:
            # Create the frontline response prompt
            prompt = self._create_frontline_prompt(alarm_text, analysis)

            # Run the agent
            response = self.agent(prompt)
            
            styled_log('FRONTLINE_RESPONSE_BOT', str(response), 'blue')

            return {
                "alarm_text": alarm_text,
                "analysis": analysis,
                "response": str(response),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Frontline response action failed: {e}")
            return {
                "alarm_text": alarm_text,
                "analysis": analysis,
                "error": str(e),
                "status": "error"
            }

    def _create_frontline_prompt(self, alarm_text: str, analysis: str) -> str:
        """Create the frontline response prompt for the agent."""
        return f"""
You are the Frontline Response Agent.

## Notes
- The necessary information should already be available in the analysis.
- You are not allowed to significantly alter email templates.

## Goals
1. Identify the event ID from the analysis below.
  a. If the Analysis Bot didn't provide an event ID, infer it from the analysis and the Confluence documentation (The Page ID 2114420748).
2. Strictly and carefully follow the Frontline response procedure.
  a. If the procedure expects you to send emails to customers, you must lookup the email template from Confluence first. The Page ID is referenced inside the last path segment of the link to the email template. Please copy the email on the email template *verbatim*, make deviations as needed.
  b. Follow the procedures with the help of tools, such as contacting customers, creating a maintenance window, or sending an email.
  c. Follow strict protocol, do not deviate from the documentation.

## Error Message
{alarm_text}

## Analysis Bot
{analysis}
        """.strip()