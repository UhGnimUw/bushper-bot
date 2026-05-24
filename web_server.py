#!/usr/bin/env python
"""Minimal web chat server — calls the agent via a clean HTTP API."""
import uuid
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Agent imports
from src.agent.agent import get_agent
from src.agent.agmem import session_store


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Lifespan ────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agent web server started")
    yield
    logger.info("Agent web server stopped")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Agent Chat", lifespan=lifespan)


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


# ── API ────────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id or str(uuid.uuid4())
    try:
        agent = get_agent(req.message)
        if agent is None:
            raise HTTPException(status_code=400, detail="无法理解意图")
        response = agent.invoke(req.message, session_id)
        return ChatResponse(response=response, session_id=session_id)
    except Exception as e:
        logger.error("chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear/{session_id}")
def clear(session_id: str) -> dict:
    session_store.clear_session(session_id)
    return {"ok": True, "session_id": session_id}


# ── HTML UI ───────────────────────────────────────────────────────────────────

HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Chat</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
  header { background: #fff; border-bottom: 1px solid #e1e4e8; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 16px; font-weight: 600; color: #1d2129; }
  #clear-btn { background: none; border: 1px solid #d0d4da; border-radius: 6px; padding: 5px 12px; font-size: 13px; cursor: pointer; color: #606770; }
  #clear-btn:hover { background: #f7f8fa; }
  #chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 72%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
  .msg.user { align-self: flex-end; background: #0084ff; color: #fff; border-bottom-right-radius: 4px; }
  .msg.assistant { align-self: flex-start; background: #fff; color: #1d2129; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }
  .msg.error { background: #fff2f0; color: #c00; border: 1px solid #ffc; }
  #input-bar { background: #fff; border-top: 1px solid #e1e4e8; padding: 12px 16px; display: flex; gap: 10px; }
  #input { flex: 1; border: 1px solid #d0d4da; border-radius: 8px; padding: 8px 12px; font-size: 14px; outline: none; }
  #input:focus { border-color: #0084ff; }
  #send { background: #0084ff; color: #fff; border: none; border-radius: 8px; padding: 8px 16px; font-size: 14px; cursor: pointer; }
  #send:disabled { opacity: 0.5; cursor: default; }
  .thinking { color: #8a8a8a; font-size: 13px; padding: 4px 0; }
</style>
</head>
<body>

<header>
  <h1>🤖 Agent Chat</h1>
  <button id="clear-btn" onclick="doClear()">清除历史</button>
</header>

<div id="chat"></div>

<div id="input-bar">
  <input id="input" placeholder="输入消息..." autofocus onkeydown="if(event.key==='Enter' && !event.shiftKey) sendMsg()">
  <button id="send" onclick="sendMsg()">发送</button>
</div>

<script>
let session_id = '';
let busy = false;

function addMsg(role, text) {
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function setThinking(on) {
  const existing = document.getElementById('thinking');
  if (on) {
    if (!existing) {
      const div = document.createElement('div');
      div.id = 'thinking';
      div.className = 'msg assistant thinking';
      div.textContent = '思考中...';
      document.getElementById('chat').appendChild(div);
    }
  } else if (existing) existing.remove();
  document.getElementById('send').disabled = on;
  busy = on;
}

async function sendMsg() {
  if (busy) return;
  const inp = document.getElementById('input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  addMsg('user', text);
  setThinking(true);
  try {
    const body = JSON.stringify({ message: text, session_id: session_id || null });
    const res = await fetch('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    session_id = data.session_id;
    setThinking(false);
    addMsg('assistant', data.response);
  } catch(e) {
    setThinking(false);
    addMsg('error', '错误: ' + e.message);
  }
}

async function doClear() {
  if (!session_id) return;
  await fetch('/clear/' + session_id, { method: 'DELETE' });
  document.getElementById('chat').innerHTML = '';
  session_id = '';
}

document.getElementById('input').focus();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
