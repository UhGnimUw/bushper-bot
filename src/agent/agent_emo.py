"""Emotional chat agent — empathetic conversation with memory.

Singleton: use get_emo_agent() from agent.py to get the instance.
"""
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from src.agent.llm import base_llm
from src.agent.agmem import get_session_history


class EmoAgent:
    """Emotional support agent — empathetic conversation with session memory.

    Singleton — get instance via get_emo_agent() in agent.py.
    """
    _instance = None

    def __new__(cls,
                 system_prompt: str = (
                     "你是一个温暖、有同理心的倾听者。当用户分享他们的感受时，"
                     "请给予理解、支持和鼓励。不要评判，不要给硬性建议，"
                     "而是帮助用户梳理情绪，理解自己的感受。"
                     "如果用户表达负面情绪（如压力、焦虑、悲伤），请先共情，再引导。"
                 )):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._system_prompt = system_prompt
            cls._instance._built = False
        return cls._instance

    def _ensure_built(self):
        if self._built:
            return
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        chain = prompt | base_llm
        self.with_memory = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        self._built = True

    def invoke(self, user_input: str, session_id: str) -> str:
        self._ensure_built()
        result = self.with_memory.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id, "thread_id": session_id}},
        )
        if hasattr(result, "content"):
            return result.content
        return str(result)
