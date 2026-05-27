"""Agent router — unified .invoke(user_input, session_id) -> str interface.

Delegates to langgraph_agent as the main entry point.
"""
import logging
from dataclasses import dataclass
from src.agent.langgraph_agent import invoke as langgraph_invoke


logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    text: str
    needs_human_input: bool = False


class AgentWrapper:
    """Wrap langgraph_invoke so it has .invoke() method for backward compatibility."""
    def invoke(self, user_input: str, session_id: str = None):
        text, needs_human_input = langgraph_invoke(user_input, session_id or "default")
        return text, needs_human_input


def get_agent(user_input: str = None, session_id: str = None):
    """Return unified agent: .invoke(user_input, session_id) -> AgentResponse."""
    return AgentWrapper()