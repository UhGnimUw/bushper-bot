"""Feishu Task Agent — handles scheduled messages, meeting booking, and meeting notes.

Singleton: use get_feishu_task_agent() from agent.py to get the instance.
"""
import logging
from langchain.agents.factory import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from src.agent.llm import base_llm
from src.agent.agmem import get_session_history, get_checkpointer
from src.agent.Tools.tool import task_tool_list

logger = logging.getLogger(__name__)


class FeishuTaskAgent:
    """Feishu task agent — handles scheduled messages, meeting booking, and meeting notes.

    Singleton — get instance via get_feishu_task_agent() in agent.py.
    """
    _instance = None

    def __new__(cls, system_prompt: str = (
        "你是一个飞书任务助手，帮助用户管理日程和任务。你可以：\n"
        "1. 定时发送消息到群组（使用schedule_message工具）\n"
        "2. 预定会议（使用create_meeting工具）\n"
        "3. 记录会议纪要（使用create_meeting_minutes工具）\n\n"
        "当你需要调用工具时，请使用提供的工具。"
    )):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._system_prompt = system_prompt
            cls._instance._built = False
        return cls._instance

    def _ensure_built(self, user_input: str = ""):
        if self._built:
            return
        self._agent = create_agent(
            model=base_llm,
            tools=task_tool_list,
            checkpointer=get_checkpointer(),
            system_prompt=self._system_prompt,
        )
        self.with_history = RunnableWithMessageHistory(
            self._agent,
            get_session_history,
            input_messages_key="messages",
            history_messages_key="chat_history",
        )
        self._built = True

    def invoke(self, user_input: str, session_id: str) -> str:
        self._ensure_built(user_input=user_input)
        response = self.with_history.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"session_id": session_id, "thread_id": session_id}},
        )
        messages = response.get("messages", []) if isinstance(response, dict) else response
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content
        return str(response)
