"""Agent router — unified .invoke(user_input, session_id) -> str interface."""
import logging
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from src.agent.llm import base_llm
from src.agent.intend import intend_map
from src.agent.agent_react import ReActAgent
from src.agent.agent_rag import RAGAgent
from src.agent.agent_emo import EmoAgent
from src.agent.agent_feishu_task import FeishuTaskAgent
from src.agent.agmem import get_session_history, session_store


logger = logging.getLogger(__name__)


class IntendForecast(BaseModel):
    intend: str = Field(description="用户意图")


def NLU(user_input: str, session_id: str = None) -> IntendForecast:
    """Intent classification — history provides prior user messages for context."""
    from langchain_core.messages import SystemMessage, HumanMessage

    messages = [
        SystemMessage(content=f"请根据用户输入，判断用户意图。用户意图只能是以下之一。{intend_map}"),
        HumanMessage(content=f"用户输入: {user_input}"),
    ]
    return base_llm.with_structured_output(IntendForecast).invoke(messages)


# Singleton agent instances
_react = ReActAgent()
_rag = RAGAgent()
_emo = EmoAgent()
_feishu_task = FeishuTaskAgent()


class AgentWithMemory:
    """Wrap a Runnable so invoke(user_input, session_id) -> str is consistent."""
    def __init__(self, runnable):
        self._runnable = runnable

    def invoke(self, user_input: str, session_id: str) -> str:
        result = self._runnable.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"session_id": session_id}},
        )
        return result[-1].content if hasattr(result[-1], "content") else str(result)


class RAGWithMemory:
    """RAG: tier-aware retrieval + history-aware synthesis."""
    def __init__(self, rag_agent):
        self._rag = rag_agent

    def invoke(self, user_input: str, session_id: str) -> str:
        return self._rag.invoke(user_input, session_id)


def get_agent(user_input: str, session_id: str = None):
    """Return unified agent: .invoke(user_input, session_id) -> str."""
    user_intend = NLU(user_input, session_id)
    logger.info('用户意图: %s', user_intend.intend)

    if user_intend.intend == "agent_tools":
        return _react

    if user_intend.intend == "query_knowledge":
        return RAGWithMemory(_rag)

    if user_intend.intend == "emotion_chat":
        return _emo

    if user_intend.intend == "feishu_task":
        return _feishu_task

    return None
