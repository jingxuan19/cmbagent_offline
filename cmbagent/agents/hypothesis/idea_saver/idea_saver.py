"""
Idea Saver Agent - Non-LLM agent that saves ideas to a JSON file.

This agent replaces the LLM-based idea_saver with a pure Python implementation.
It parses the formatted ideas from idea_maker_response_formatter and saves them
to a JSON file.
"""

import os
import re
import json
import datetime
from cmbagent.base_agent import BaseAgent
from autogen.agentchat import ConversableAgent


def _parse_ideas_from_formatted_text(text: str) -> list[dict]:
    """
    Parse ideas from the formatted text output of idea_maker_response_formatter.

    Expected format:
    **Ideas**
    - Idea 1:
        * idea title here
            - bullet point 1
            - bullet point 2
    - Idea 2:
        * another idea title
            - bullet point 1

    Returns:
        List of dicts with 'idea_description' and 'bullet_points' keys.
    """
    ideas = []

    # Split by "- Idea N:" pattern
    idea_pattern = r'-\s*Idea\s+\d+:'
    parts = re.split(idea_pattern, text)

    for part in parts[1:]:  # Skip the first part (before "- Idea 1:")
        if not part.strip():
            continue

        idea = {
            'idea_description': '',
            'bullet_points': []
        }

        lines = part.strip().split('\n')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if it's the idea title (starts with *)
            if stripped.startswith('* '):
                idea['idea_description'] = stripped[2:].strip()
            # Check if it's a bullet point (starts with -)
            elif stripped.startswith('- '):
                idea['bullet_points'].append(stripped[2:].strip())

        if idea['idea_description']:
            ideas.append(idea)

    return ideas


class IdeaSaverAgent(BaseAgent):
    """Non-LLM agent that saves ideas to a JSON file."""

    def __init__(self, llm_config=None, **kwargs):
        agent_id = os.path.splitext(os.path.abspath(__file__))[0]
        # Pass llm_config to parent but we won't use it
        super().__init__(llm_config=llm_config, agent_id=agent_id, **kwargs)

    def set_agent(self, **kwargs):
        """Create a non-LLM agent that saves ideas."""
        self.agent = IdeaSaverConversableAgent(
            name=self.name,
            description=self.info.get("description", "Idea saver agent"),
            llm_config=False,  # No LLM needed
            human_input_mode="NEVER",
            work_dir=self.work_dir,
        )


class IdeaSaverConversableAgent(ConversableAgent):
    """
    A ConversableAgent that doesn't use LLM.
    Instead, it parses and saves ideas from the formatted text.
    """

    def __init__(self, work_dir: str = ".", **kwargs):
        self._work_dir = work_dir
        super().__init__(**kwargs)
        # Register our custom reply function
        self.register_reply(
            trigger=lambda sender: True,  # Reply to any sender
            reply_func=self._save_ideas_reply,
            position=0,  # High priority
        )

    def _save_ideas_reply(
        self,
        recipient: ConversableAgent,
        messages: list[dict],
        sender: ConversableAgent,
        config: dict,
    ) -> tuple[bool, str]:
        """
        Parse ideas from the last message and save to JSON file.

        Returns:
            Tuple of (True, message) indicating the reply was generated.
        """
        if not messages:
            return True, "No message to process."

        last_message = messages[-1]
        content = last_message.get("content", "")

        # Parse ideas from formatted text
        ideas = _parse_ideas_from_formatted_text(content)

        if not ideas:
            return True, "No ideas found in the message."

        # Save to JSON file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self._work_dir, f'ideas_{timestamp}.json')

        try:
            with open(filepath, 'w') as f:
                json.dump(ideas, f, indent=2)
            return True, f"\nIdeas saved in {filepath}\n"
        except Exception as e:
            return True, f"\nFailed to save ideas: {e}\n"
