"""
Review Recorder Agent - Non-LLM agent that records plan reviews.

This agent replaces the LLM-based review_recorder with a pure Python implementation.
It extracts the recommendations from the formatted review message and updates
context_variables accordingly.
"""

import os
from cmbagent.base_agent import BaseAgent
from autogen.agentchat import ConversableAgent


class ReviewRecorderAgent(BaseAgent):
    """Non-LLM agent that records plan reviews."""

    def __init__(self, llm_config=None, **kwargs):
        agent_id = os.path.splitext(os.path.abspath(__file__))[0]
        # Pass llm_config to parent but we won't use it
        super().__init__(llm_config=llm_config, agent_id=agent_id, **kwargs)

    def set_agent(self, **kwargs):
        """Create a non-LLM agent that records reviews."""
        self.agent = ReviewRecorderConversableAgent(
            name=self.name,
            description=self.info.get("description", "Review recorder agent"),
            llm_config=False,  # No LLM needed
            human_input_mode="NEVER",
        )


class ReviewRecorderConversableAgent(ConversableAgent):
    """
    A ConversableAgent that doesn't use LLM.
    Instead, it records the review and updates context_variables.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Register our custom reply function
        self.register_reply(
            trigger=lambda sender: True,  # Reply to any sender
            reply_func=self._record_review_reply,
            position=0,  # High priority
        )

    def _record_review_reply(
        self,
        recipient: ConversableAgent,
        messages: list[dict],
        sender: ConversableAgent,
        config: dict,
    ) -> tuple[bool, str]:
        """
        Record the review from the last message and update context_variables.

        Returns:
            Tuple of (True, message) indicating the reply was generated.
        """
        if not messages:
            return True, "No message to process."

        last_message = messages[-1]
        content = last_message.get("content", "")

        # The review content is the full message from reviewer_response_formatter
        plan_review = content

        # Update context_variables (accessed via the agent's context)
        ctx = self.context_variables

        # Record the review
        reviews = ctx.get("reviews", [])
        if not isinstance(reviews, list):
            reviews = []
        reviews.append(plan_review)
        ctx["reviews"] = reviews
        ctx["recommendations"] = plan_review

        # Decrement feedback rounds left
        feedback_left = ctx.get("feedback_left", 1)
        feedback_left = max(0, feedback_left - 1)
        ctx["feedback_left"] = feedback_left

        return True, f"""
Recommendations have been logged.
Number of feedback rounds left: {feedback_left}.
Now, update the plan accordingly, planner!"""
