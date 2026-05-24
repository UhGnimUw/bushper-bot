# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Feishu (Lark) Stream bot with an agent-based architecture. It uses LangChain for LLM orchestration, supports multiple agent types (ReAct, RAG), and executes shell scripts for agent capabilities.

## Entry Point

- `feishu.py` — Feishu Stream bot. Run with: `python feishu.py --app_id XXX --app_secret XXX`

## Commands

```bash
conda activate finrpa
# Run the bot
python feishu.py

# Run web chat UI (http://localhost:8000)
python web_server.py

# Run agent tests
python src/agent/agent_rag.py
python src/agent/agent_react.py
```

## Architecture

### Agent System (`src/agent/`) — All singleton classes
- `agent.py` — Intent classification + `get_agent()` returning unified `agent.invoke(user_input, session_id)` interface
- `agent_react.py` — `ReActAgent` singleton; LangGraph `create_agent` with `ToolNode`, lazy-built on first invoke
- `agent_emo.py` — `EmoAgent` singleton; pure LLM emotional chat, lazy-built
- `agent_rag.py` — `RAGAgent` singleton; ChromaDB RAG, chain built lazily on first `invoke()`
- `agmem.py` — `SessionHistoryStore` singleton; `ChatMessageHistory` per session
- `intend.py` — Intent map: `agent_tools`, `quary_knowledge`, `emotion_chat`

### Unified Agent Interface
`get_agent()` returns an object with `.invoke(user_input, session_id) -> str`:
- `agent_tools` → `ReActAgent` (multi-step tool use with reasoning + memory)
- `quary_knowledge` → `RAGWithMemory(RAGAgent)` (stateless, session_id accepted for compatibility)
- `emotion_chat` → `EmoAgent` (empathetic conversation + memory)

### Memory (`agmem.py`)
- `SessionHistoryStore` singleton — `ChatMessageHistory` per session (in-memory)
- `get_session_history(session_id)` — callable for `RunnableWithMessageHistory`
- `session_store.clear_session(session_id)` — clears history (used for "清除历史" command)
- For SQLite persistence: upgrade langgraph to ≥0.3.x and use `SqliteSaver`

### Tools (`src/agent/Tools/tool.py`)
Decorated with `@tool`. Current tools: `get_stock_price`, `search_news`, `get_current_weather`, `calculate`, `search_knowledge`, `search_web` (mock).

### Shell Script Execution (`.king_rule.md`)
Low-risk and high-risk command scripts with safety checks: first-generation review, dangerous parameter validation, final permission checks. Uses absolute paths.

### Key Dependencies
- `langchain` 1.2.x / `langchain-core` — Agent orchestration via `create_agent` (LangGraph)
- `langgraph` 1.1.x — `InMemorySaver` checkpointer, `ToolNode`
- `langchain-community` — ChromaDB vectorstore, `ChatMessageHistory`
- `lark_oapi` — Feishu API
- `chromadb` — Vector database for RAG
- `fastapi` / `uvicorn` — Web chat server

## Directory Structure

```
feishu.py          # Feishu Stream bot
web_server.py       # Web chat server (FastAPI, http://localhost:8000)
src/agent/          # Core agent logic
  Tools/tool.py     # Tool definitions
llm/               # LLM configurations
MCP/               # MCP server integrations
skill/             # Custom skill system
Task/              # Task-related code
reference/         # Reference materials
chroma_db/         # Persisted vector database
```