"""ReAct agent — multi-step tool calling with reasoning and memory.

Singleton: use get_react_agent() from agent.py to get the instance.
"""
import sys
from pathlib import Path

_agent_dir = Path(__file__).parent
sys.path.insert(0, str(_agent_dir))

from langchain.agents.factory import create_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage

from Tools.tool import tool_list as _tool_list  # noqa: E402
from src.agent.llm import base_llm  # noqa: E402
from src.agent.agmem import get_session_history, get_checkpointer  # noqa: E402
from src.agent.skill_manager import build_skill_context_for_prompt  # noqa: E402
import logging
logger = logging.getLogger(__name__)

class ReActAgent:
    """ReAct agent — multi-step tool use with reasoning + session memory.

    Singleton — get instance via get_react_agent() in agent.py.
    """
    _instance = None

    def __new__(cls, system_prompt: str = "你是一个智能助手，可以使用工具和技能来帮助用户解决问题。"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._system_prompt = system_prompt
        return cls._instance

    def _ensure_built(self, user_input: str = ""):
        # Build skill context via progressive disclosure, using user's actual input
        skill_context = build_skill_context_for_prompt(user_input)
        logger.info(f"ReActAgent skill context: {skill_context}")
        if skill_context:
            full_prompt = f"{self._system_prompt}\n\n skill有：{skill_context}"
        else:
            full_prompt = self._system_prompt
        logger.info(f"ReActAgent system prompt: {full_prompt}")
        self._agent = create_agent(
            model=base_llm,
            tools=_tool_list,
            checkpointer=get_checkpointer(),
            system_prompt=full_prompt,
        )
        self.with_history = RunnableWithMessageHistory(
            self._agent,
            get_session_history,
            input_messages_key="messages",
            history_messages_key="chat_history",
        )

    def invoke(self, user_input: str, session_id: str) -> str:
        self._ensure_built(user_input=user_input)
        response = self.with_history.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"session_id": session_id, "thread_id": session_id}},
        )
        # response 是 dict {"messages": [...]} — 取最后一条 AI 消息
        messages = response.get("messages", []) if isinstance(response, dict) else response
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content
        return str(response)


if __name__ == "__main__":
    from src.agent.agmem import session_store

    react = ReActAgent()
    print("ReActAgent singleton OK")
