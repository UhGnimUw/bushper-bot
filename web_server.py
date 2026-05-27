#!/usr/bin/env python
"""Minimal web chat server — calls the agent via a clean HTTP API."""
import uuid
import logging
import time
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
from src.agent.db_service import init_db, log_metrics, get_recent_metrics, get_metrics_summary
from src.agent.db_service import get_feishu_conversations, get_feishu_sessions
from src.agent.Tools.city_graph_tool import search_city_graph


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Lifespan ────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agent web server started")
    init_db()
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
    needs_human_input: bool = False


# ── API ────────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    start_time = time.time()
    session_id = req.session_id or str(uuid.uuid4())
    try:
        agent = get_agent(req.message)
        if agent is None:
            raise HTTPException(status_code=400, detail="无法理解意图")
        response, needs_human_input = agent.invoke(req.message, session_id)
        response_time_ms = (time.time() - start_time) * 1000
        log_metrics(response_time_ms=response_time_ms, request_count=1)
        return ChatResponse(response=response, session_id=session_id, needs_human_input=needs_human_input)
    except Exception as e:
        logger.error("chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear/{session_id}")
def clear(session_id: str) -> dict:
    session_store.clear_session(session_id)
    return {"ok": True, "session_id": session_id}


# ── Monitor API ────────────────────────────────────────────────────────────────

@app.get("/api/monitor/stats")
def monitor_stats() -> dict:
    """Get metrics summary for monitoring."""
    try:
        summary = get_metrics_summary(hours=24)
        return {
            "ok": True,
            "summary": summary,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("monitor stats error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/recent")
def monitor_recent(hours: int = 24, limit: int = 100) -> dict:
    """Get recent metrics entries."""
    try:
        metrics = get_recent_metrics(hours=hours, limit=limit)
        return {"ok": True, "metrics": metrics}
    except Exception as e:
        logger.error("monitor recent error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Feishu Conversations API ──────────────────────────────────────────────────

@app.get("/api/feishu/conversations")
def feishu_conversations(session_id: str = None, limit: int = 50) -> dict:
    """Get Feishu conversations."""
    try:
        conversations = get_feishu_conversations(session_id=session_id, limit=limit)
        return {"ok": True, "conversations": conversations}
    except Exception as e:
        logger.error("feishu conversations error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feishu/sessions")
def feishu_sessions(limit: int = 20) -> dict:
    """Get distinct Feishu sessions."""
    try:
        sessions = get_feishu_sessions(limit=limit)
        return {"ok": True, "sessions": sessions}
    except Exception as e:
        logger.error("feishu sessions error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── City Graph API ──────────────────────────────────────────────────────────────

@app.get("/api/graph/data")
def graph_data() -> dict:
    """Get graph data for D3.js visualization."""
    import json
    from pathlib import Path
    relation_file = Path(__file__).parent / "graph_view" / "html" / "relation.json"
    if not relation_file.exists():
        return {"ok": False, "error": "Graph data not found"}
    try:
        with open(relation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.error("graph data error: %s", e)
        return {"ok": False, "error": str(e)}


@app.get("/api/graph/answer")
def graph_answer(q: str) -> dict:
    """Query the city graph."""
    try:
        result = search_city_graph.invoke({"query": q})
        return {"ok": True, "answer": result}
    except Exception as e:
        logger.error("graph answer error: %s", e)
        return {"ok": False, "error": str(e)}


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
  header nav { display: flex; gap: 16px; }
  header nav a { color: #606770; text-decoration: none; font-size: 14px; }
  header nav a:hover, header nav a.active { color: #0084ff; }
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
  <nav>
    <a href="/" onclick="showView('chat')" class="active">对话</a>
    <a href="/monitor" onclick="showView('monitor')">监控</a>
    <a href="/feishu" onclick="showView('feishu')">飞书会话</a>
  </nav>
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
    if (data.needs_human_input) {
      const badge = document.createElement('div');
      badge.style.cssText = 'margin-top:6px;font-size:12px;color:#0084ff;font-weight:500';
      badge.textContent = '💡 请补充上述信息后再次发送';
      document.querySelector('.msg.assistant:last-child').appendChild(badge);
    }
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

MONITOR_HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>系统监控</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
  header { background: #fff; border-bottom: 1px solid #e1e4e8; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 16px; font-weight: 600; color: #1d2129; }
  header nav { display: flex; gap: 16px; }
  header nav a { color: #606770; text-decoration: none; font-size: 14px; }
  header nav a:hover, header nav a.active { color: #0084ff; }
  .container { flex: 1; padding: 20px; overflow-y: auto; }
  .card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }
  .card h2 { font-size: 16px; color: #1d2129; margin-bottom: 12px; }
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
  .stat { padding: 16px; background: #f7f8fa; border-radius: 6px; }
  .stat-label { font-size: 13px; color: #606770; margin-bottom: 4px; }
  .stat-value { font-size: 24px; font-weight: 600; color: #1d2129; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #e1e4e8; }
  th { font-size: 13px; color: #606770; font-weight: 500; }
  td { font-size: 14px; color: #1d2129; }
  tr:hover { background: #f7f8fa; }
</style>
</head>
<body>
<header>
  <h1>📊 系统监控</h1>
  <nav>
    <a href="/">对话</a>
    <a href="/monitor" class="active">监控</a>
    <a href="/feishu">飞书会话</a>
  </nav>
</header>
<div class="container">
  <div class="card">
    <h2>24小时统计概览</h2>
    <div class="stats-grid" id="stats-grid">
      <div class="stat">
        <div class="stat-label">总请求数</div>
        <div class="stat-value" id="total-requests">-</div>
      </div>
      <div class="stat">
        <div class="stat-label">平均响应时间</div>
        <div class="stat-value" id="avg-response">-</div>
      </div>
      <div class="stat">
        <div class="stat-label">最大响应时间</div>
        <div class="stat-value" id="max-response">-</div>
      </div>
      <div class="stat">
        <div class="stat-label">平均CPU</div>
        <div class="stat-value" id="avg-cpu">-</div>
      </div>
    </div>
  </div>
  <div class="card">
    <h2>最近请求记录</h2>
    <table>
      <thead>
        <tr>
          <th>时间</th>
          <th>响应时间(ms)</th>
          <th>请求数</th>
        </tr>
      </thead>
      <tbody id="metrics-tbody">
      </tbody>
    </table>
  </div>
</div>
<script>
async function loadStats() {
  try {
    const res = await fetch('/api/monitor/stats');
    const data = await res.json();
    if (data.ok) {
      const s = data.summary;
      document.getElementById('total-requests').textContent = s.total_requests || 0;
      document.getElementById('avg-response').textContent = s.avg_response_time ? s.avg_response_time.toFixed(2) + 'ms' : '-';
      document.getElementById('max-response').textContent = s.max_response_time ? s.max_response_time.toFixed(2) + 'ms' : '-';
      document.getElementById('avg-cpu').textContent = s.avg_cpu ? s.avg_cpu.toFixed(1) + '%' : '-';
    }
  } catch(e) { console.error(e); }
}

async function loadRecent() {
  try {
    const res = await fetch('/api/monitor/recent?hours=24&limit=50');
    const data = await res.json();
    if (data.ok) {
      const tbody = document.getElementById('metrics-tbody');
      tbody.innerHTML = '';
      data.metrics.forEach(m => {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td>' + new Date(m.timestamp).toLocaleString() + '</td><td>' + (m.response_time_ms ? m.response_time_ms.toFixed(2) : '-') + '</td><td>' + (m.request_count || 0) + '</td>';
        tbody.appendChild(tr);
      });
    }
  } catch(e) { console.error(e); }
}

loadStats();
loadRecent();
setInterval(function() { loadStats(); loadRecent(); }, 30000);
</script>
</body>
</html>
"""

FEISHU_HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>飞书会话</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
  header { background: #fff; border-bottom: 1px solid #e1e4e8; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 16px; font-weight: 600; color: #1d2129; }
  header nav { display: flex; gap: 16px; }
  header nav a { color: #606770; text-decoration: none; font-size: 14px; }
  header nav a:hover, header nav a.active { color: #0084ff; }
  .container { flex: 1; padding: 20px; overflow-y: auto; display: flex; gap: 20px; }
  .sessions { width: 300px; background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }
  .conversations { flex: 1; background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.08); overflow-y: auto; }
  .sessions h2, .conversations h2 { font-size: 16px; color: #1d2129; margin-bottom: 12px; }
  .session-item { padding: 12px; border-radius: 6px; cursor: pointer; margin-bottom: 8px; }
  .session-item:hover { background: #f7f8fa; }
  .session-item.active { background: #e8f0fe; }
  .session-name { font-size: 14px; font-weight: 500; color: #1d2129; }
  .session-meta { font-size: 12px; color: #606770; margin-top: 4px; }
  .conv-item { padding: 12px; border-bottom: 1px solid #e1e4e8; }
  .conv-item:last-child { border-bottom: none; }
  .conv-user { font-size: 14px; font-weight: 500; color: #0084ff; }
  .conv-assistant { font-size: 14px; color: #1d2129; margin-top: 8px; }
  .conv-time { font-size: 12px; color: #606770; margin-top: 4px; }
  .empty { text-align: center; color: #606770; padding: 40px; }
</style>
</head>
<body>
<header>
  <h1>💬 飞书会话</h1>
  <nav>
    <a href="/">对话</a>
    <a href="/monitor">监控</a>
    <a href="/feishu" class="active">飞书会话</a>
  </nav>
</header>
<div class="container">
  <div class="sessions">
    <h2>会话列表</h2>
    <div id="session-list"></div>
  </div>
  <div class="conversations">
    <h2>对话详情</h2>
    <div id="conv-detail"><div class="empty">请选择左侧会话查看详情</div></div>
  </div>
</div>
<script>
let selectedSession = null;

async function loadSessions() {
  try {
    const res = await fetch('/api/feishu/sessions?limit=50');
    const data = await res.json();
    if (data.ok) {
      const list = document.getElementById('session-list');
      list.innerHTML = '';
      data.sessions.forEach(s => {
        const div = document.createElement('div');
        div.className = 'session-item' + (selectedSession === s.session_id ? ' active' : '');
        div.innerHTML = '<div class="session-name">' + (s.user_name || s.session_id) + '</div><div class="session-meta">' + s.message_count + '条消息 | ' + new Date(s.last_message).toLocaleString() + '</div>';
        div.onclick = function() { selectedSession = s.session_id; loadSessions(); loadConversations(s.session_id); };
        list.appendChild(div);
      });
    }
  } catch(e) { console.error(e); }
}

async function loadConversations(sessionId) {
  try {
    const res = await fetch('/api/feishu/conversations?session_id=' + sessionId + '&limit=50');
    const data = await res.json();
    if (data.ok) {
      const detail = document.getElementById('conv-detail');
      if (data.conversations.length === 0) {
        detail.innerHTML = '<div class="empty">暂无对话记录</div>';
        return;
      }
      detail.innerHTML = '';
      data.conversations.reverse().forEach(c => {
        const div = document.createElement('div');
        div.className = 'conv-item';
        div.innerHTML = '<div class="conv-user">用户: ' + c.message + '</div>' + (c.response ? '<div class="conv-assistant">助手: ' + c.response + '</div>' : '') + '<div class="conv-time">' + new Date(c.timestamp).toLocaleString() + '</div>';
        detail.appendChild(div);
      });
    }
  } catch(e) { console.error(e); }
}

loadSessions();
setInterval(loadSessions, 30000);
</script>
</body>
</html>
"""

GRAPH_HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中国城市知识图谱</title>
<script src="https://cdn.bootcss.com/jquery/2.1.4/jquery.min.js"></script>
<link href="https://cdn.bootcss.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.bootcss.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>
<script src="https://d3js.org/d3.v4.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 30px 40px;
    min-height: 100vh;
    font-family: OpenSans-Light, PingFang SC, Hiragino Sans GB, Microsoft Yahei, sans-serif;
}
h1 { color: #fff; font-size: 28px; margin-bottom: 20px; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.graph-container { display: flex; gap: 20px; height: calc(100vh - 120px); }
.graph-main { flex: 1; background: rgba(255,255,255,0.95); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); overflow: hidden; display: flex; flex-direction: column; }
.graph-svg-wrapper { flex: 1; overflow: auto; padding: 10px; }
#svg1 { display: block; margin: 0 auto; }
.sidebar { width: 280px; display: flex; flex-direction: column; gap: 16px; }
.sidebar-card { background: rgba(255,255,255,0.95); border-radius: 12px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.sidebar-card h3 { font-size: 14px; color: #1d2129; margin-bottom: 12px; font-weight: 600; }
#indicator div { margin-bottom: 6px; font-size: 13px; color: #606770; }
#indicator span { display: inline-block; width: 20px; height: 12px; border-radius: 3px; margin-right: 8px; vertical-align: middle; }
#mode { display: flex; gap: 0; }
#mode span { padding: 6px 14px; border: 1px solid #e1e4e8; font-size: 13px; cursor: pointer; transition: all 0.2s; }
#mode span:first-child { border-radius: 6px 0 0 6px; }
#mode span:last-child { border-radius: 0 6px 6px 0; border-left: none; }
#mode span.active { background: #0084ff; color: #fff; border-color: #0084ff; }
#mode span:not(.active):hover { background: #f0f8ff; }
#info { font-size: 12px; }
#info h4 { font-size: 15px; margin-bottom: 8px; }
#info p { color: #606770; margin-bottom: 4px; }
#info p span { color: #1d2129; margin-right: 8px; font-weight: 500; }
.search-box { display: flex; gap: 8px; }
.search-box input { flex: 1; border: 1px solid #e1e4e8; border-radius: 6px; padding: 8px 12px; font-size: 13px; outline: none; }
.search-box input:focus { border-color: #0084ff; }
.search-box button { background: #0084ff; color: #fff; border: none; border-radius: 6px; padding: 8px 16px; font-size: 13px; cursor: pointer; }
.search-box button:hover { background: #0073e6; }
#answer-result { margin-top: 12px; padding: 10px; background: #f7f8fa; border-radius: 6px; font-size: 12px; color: #1d2129; line-height: 1.6; max-height: 200px; overflow-y: auto; }
.links line { stroke: #ccc; stroke-opacity: 0.6; }
.links line.inactive { stroke-opacity: 0; }
.nodes circle { stroke: #fff; stroke-width: 1.5px; cursor: pointer; }
.nodes circle:hover { opacity: 0.8; }
.nodes circle.inactive { display: none; }
.texts text { font-size: 11px; cursor: pointer; }
.texts text:hover { opacity: 0.7; }
.texts text.inactive { display: none; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 3px; }
::-webkit-scrollbar-track { background: transparent; }
</style>
</head>
<body>
<header style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
  <h1 style="margin:0;">🌆 中国主要城市信息知识图谱</h1>
  <nav style="display:flex; gap:16px;">
    <a href="/" style="color:#fff; text-decoration:none; font-size:14px; padding:6px 12px; border-radius:6px;">对话</a>
    <a href="/graph" style="color:#fff; background:rgba(255,255,255,0.2); text-decoration:none; font-size:14px; padding:6px 12px; border-radius:6px;">知识图谱</a>
    <a href="/monitor" style="color:#fff; text-decoration:none; font-size:14px; padding:6px 12px; border-radius:6px;">监控</a>
    <a href="/feishu" style="color:#fff; text-decoration:none; font-size:14px; padding:6px 12px; border-radius:6px;">飞书会话</a>
  </nav>
</header>
<div class="graph-container">
  <div class="graph-main">
    <div class="graph-svg-wrapper">
      <svg width="1400" height="800" id="svg1"></svg>
    </div>
  </div>
  <div class="sidebar">
    <div class="sidebar-card">
      <h3>图例</h3>
      <div id="indicator">
        <div><span style="background:#6ca46c;"></span>行政级别</div>
        <div><span style="background:#4e88af;"></span>省份</div>
        <div><span style="background:#ca635f;"></span>城市</div>
      </div>
      <div id="mode" style="margin-top:12px;">
        <span class="active">图形</span>
        <span>文字</span>
      </div>
    </div>
    <div class="sidebar-card">
      <h3>节点信息</h3>
      <div id="info"><h4 style="color:#8a8a8a;">悬停查看详情</h4></div>
    </div>
    <div class="sidebar-card">
      <h3>问答查询</h3>
      <div class="search-box">
        <input type="text" id="form-control" placeholder="如：浙江省有哪些城市、杭州市的人口...">
        <button id="bnt-search">查询</button>
      </div>
      <div id="answer-result"></div>
    </div>
  </div>
</div>
<script>
var svg = d3.select("#svg1"),
    width = svg.attr("width"),
    height = svg.attr("height");
var colors = ['#6ca46c', '#4e88af', '#ca635f'];
var names = ['行政级别', '城市', '省份'];

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide(30));

var graph, nodes = [], links = [], nodeSet = [];

$.ajax({
    url: "/api/graph/data",
    async: false,
    success: function(result) {
        if (result.ok) showData(result.data);
    },
    error: function() {
        alert('后端错误，请重试！');
    }
});

function showData(data) {
    graph = data;
    for (var item of graph) {
        if (nodeSet.indexOf(item.p.start.identity) == -1) {
            nodeSet.push(item.p.start.identity);
            nodes.push({
                id: item.p.start.identity,
                label: item.p.start.labels[0],
                properties: item.p.start.properties
            });
        }
        if (nodeSet.indexOf(item.p.end.identity) == -1) {
            nodeSet.push(item.p.end.identity);
            nodes.push({
                id: item.p.end.identity,
                label: item.p.end.labels[0],
                properties: item.p.end.properties
            });
        }
        links.push({
            source: item.p.segments[0].relationship.start,
            target: item.p.segments[0].relationship.end,
            type: item.p.segments[0].relationship.type,
            properties: item.p.segments[0].relationship.properties
        });
    }

    var link = svg.append("g").attr("class", "links")
        .selectAll("line").data(links).enter()
        .append("line").attr("stroke-width", 1.2);

    var node = svg.append("g").attr("class", "nodes")
        .selectAll("circle").data(nodes).enter()
        .append("circle").attr("r", function(d) {
            var size = 15;
            switch(d.label) {
                case '行政级别': size = 16; break;
                case '城市': size = 14; break;
                case '省份': size = 12; break;
                default: size = 14;
            }
            return size;
        }).attr("fill", function(d) {
            var index = 2;
            switch(d.label) {
                case '行政级别': index = 0; break;
                case '省份': index = 1; break;
                case '城市': index = 2; break;
            }
            return colors[index];
        }).attr("stroke", "#fff").attr("name", function(d) {
            return d.properties.name || d.properties.level || d.properties.province || '';
        }).attr("id", d => d.id)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    var text = svg.append("g").attr("class", "texts")
        .selectAll("text").data(nodes).enter()
        .append("text").attr("font-size", "12px").attr("fill", function(d) {
            var index = 2;
            switch(d.label) {
                case '行政级别': index = 0; break;
                case '省份': index = 1; break;
                case '城市': index = 2; break;
            }
            return colors[index];
        }).attr("name", function(d) {
            return d.properties.name || d.properties.level || d.properties.province || '';
        }).text(function(d) {
            return d.properties.name || d.properties.level || d.properties.province || '';
        });

    simulation.nodes(nodes).on("tick", ticked);
    simulation.force("link").links(links).distance(d => {
        var dist = 60;
        switch(d.source.label) {
            case '行政级别': dist += 30; break;
            case '省份': dist += 25; break;
            case '城市': dist += 20; break;
        }
        switch(d.target.label) {
            case '行政级别': dist += 30; break;
            case '省份': dist += 25; break;
            case '城市': dist += 20; break;
        }
        return dist;
    });

    function ticked() {
        link.attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        node.attr("cx", d => d.x).attr("cy", d => d.y);
        text.attr("transform", d => {
            var size = 12;
            return "translate(" + (d.x - size / 2) + "," + (d.y + size / 2) + ")";
        });
    }
}

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
}
function dragged(d) { d.fx = d3.event.x; d.fy = d3.event.y; }
function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
}

$('#mode span').click(function() {
    $('#mode span').removeClass('active');
    $(this).addClass('active');
    if ($(this).text() == '图形') {
        $('.texts text').hide();
        $('.nodes circle').show();
    } else {
        $('.texts text').show();
        $('.nodes circle').hide();
    }
});

$('#bnt-search').click(function() {
    var text = $('#form-control').val();
    if (!text) return;
    $.ajax({
        url: "/api/graph/answer?q=" + encodeURIComponent(text),
        success: function(result) {
            if (result.ok) {
                $('#answer-result').html(result.answer || '未找到相关答案');
            } else {
                $('#answer-result').html('查询失败：' + result.error);
            }
        },
        error: function() {
            $('#answer-result').html('后端错误，请重试！');
        }
    });
});

$('#svg1').on('mouseenter', '.nodes circle', function(event) {
    var name = $(this).attr("name");
    var id = $(this).attr("id");
    var fill = $(this).attr("fill");
    $('#info h4').css('color', fill).text(name);
    $('#info p').remove();
    for (var item of nodes) {
        if (item.id == id) {
            for (var key in item.properties) {
                $('#info').append('<p><span>' + key + '</span>' + item.properties[key] + '</p>');
            }
        }
    }
    d3.select('#svg1 .nodes').selectAll('circle').attr('class', function(d) {
        var n = d.properties.name || d.properties.level || d.properties.province || '';
        if (n == name) return '';
        for (var i = 0; i < links.length; i++) {
            var ts = links[i].source.properties.name || links[i].source.properties.level || '';
            var tt = links[i].target.properties.name || links[i].target.properties.level || '';
            if ((ts == name && links[i].target.id == d.id) || (tt == name && links[i].source.id == d.id)) return '';
        }
        return 'inactive';
    });
    d3.select("#svg1 .links").selectAll('line').attr('class', function(d) {
        var ts = d.source.properties.name || d.source.properties.level || '';
        var tt = d.target.properties.name || d.target.properties.level || '';
        if (ts == name || tt == name) return '';
        return 'inactive';
    });
});

$('#svg1').on('mouseleave', '.nodes circle', function(event) {
    d3.select('#svg1 .nodes').selectAll('circle').attr('class', '');
    d3.select('#svg1 .links').selectAll('line').attr('class', '');
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.get("/monitor", response_class=HTMLResponse)
def monitor():
    return MONITOR_HTML


@app.get("/feishu", response_class=HTMLResponse)
def feishu():
    return FEISHU_HTML


@app.get("/graph", response_class=HTMLResponse)
def graph():
    return GRAPH_HTML


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")