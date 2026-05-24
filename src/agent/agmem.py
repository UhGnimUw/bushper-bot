from langgraph.checkpoint.memory import InMemorySaver
from langchain_community.chat_message_histories import ChatMessageHistory


class SessionHistoryStore:
    """Per-session ChatMessageHistory store for RunnableWithMessageHistory.

    Uses in-memory dict (per-process). For multi-worker or persistent
    storage, replace get_history() with SQLChatMessageHistory backed by
    SQLite/Postgres.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._store = {}  # session_id -> ChatMessageHistory
        return cls._instance

    def get_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self._store:
            self._store[session_id] = ChatMessageHistory()
        return self._store[session_id]

    def clear_session(self, session_id: str):
        if session_id in self._store:
            self._store[session_id].clear()


# Global singleton
session_store = SessionHistoryStore()


def get_session_history(session_id: str) -> ChatMessageHistory:
    """Callable for RunnableWithMessageHistory — returns ChatMessageHistory per session."""
    return session_store.get_history(session_id)


# LangGraph agent checkpointer (in-memory, per-process)
# For SQLite persistence, langgraph >= 0.3.x provides SqliteSaver;
# for now use InMemorySaver (agent state resets on bot restart)
_checkpointer = None


def get_checkpointer():
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = InMemorySaver()
    return _checkpointer
