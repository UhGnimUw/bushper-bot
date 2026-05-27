# MyAgent - 飞书智能助手

基于 LangChain/LangGraph 的飞书智能助手，支持多Agent（RAG、ReAct、情感聊天）和知识图谱。

## 功能特性

### 1. Agent系统
- **RAG Agent** — 分层知识库检索（T0-T3权限控制）
- **ReAct Agent** — 工具调用+推理（天气、搜索、计算等）
- **情感聊天** — 情感支持对话
- **城市知识图谱** — 中国城市/省份信息查询

### 2. Web界面
- `/` — 聊天界面
- `/monitor` — 系统监控（请求统计、响应时间）
- `/feishu` — 飞书会话历史查看

### 3. 城市知识图谱工具

使用 `search_city_graph` 工具查询城市/省份信息：
- 城市基本信息（人口、GDP、车牌等）
- 城市间接壤关系
- 省份及其下辖城市

**初始化数据库：**
```bash
python -c "from src.agent.Tools.city_graph_tool import init_city_graph_db; init_city_graph_db()"
```

### 4. Vue前端（可选）

```bash
cd web
npm install
npm run dev  # 访问 http://localhost:3000
```

## 快速开始

### 1. 安装依赖
```bash
conda activate finrpa
pip install langchain langchain-core langgraph langchain-community chromadb langchain-chroma fastapi uvicorn
```

### 2. 初始化数据库
```bash
# 初始化权限数据
python test/test_permission.py --init

# 初始化城市知识图谱
python -c "from src.agent.Tools.city_graph_tool import init_city_graph_db; init_city_graph_db()"
```

### 3. 运行服务
```bash
# 飞书机器人
python feishu.py --app_id XXX --app_secret XXX

# Web聊天服务
python web_server.py  # 访问 http://localhost:8000
```


### 4. 运行测试
```bash
# 单元测试
python test/test_city_graph_tool.py
python test/test_db_service.py
python test/test_web_api.py

# Playwright E2E测试
npx playwright test
```


## 项目结构

```
myagent/
├── feishu.py              # 飞书Stream机器人
├── web_server.py          # FastAPI Web服务（含HTML界面）
├── src/agent/
│   ├── agent.py          # Agent路由
│   ├── langgraph_agent.py # LangGraph主流程
│   ├── agent_rag.py      # RAG Agent
│   ├── agent_react.py    # ReAct Agent
│   ├── Tools/
│   │   ├── tool.py       # 通用工具
│   │   └── city_graph_tool.py  # 城市知识图谱工具
│   └── db_service.py    # 监控/会话存储
├── web/                  # Vue前端（可选）
├── test/
│   ├── test_city_graph_tool.py
│   ├── test_db_service.py
│   ├── test_web_api.py
│   └── e2e/             # Playwright E2E测试
└── graph_view/html/     # 城市知识图谱可视化（参考）
```

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 发送消息 |
| DELETE | `/clear/{session_id}` | 清除会话历史 |
| GET | `/api/monitor/stats` | 获取监控统计 |
| GET | `/api/monitor/recent` | 获取最近请求 |
| GET | `/api/feishu/sessions` | 获取会话列表 |
| GET | `/api/feishu/conversations` | 获取对话详情 |

## 技术栈

- **Agent框架**: LangChain/LangGraph
- **LLM**: 本地Qwen模型
- **向量数据库**: ChromaDB
- **Web框架**: FastAPI + uvicorn
- **前端**: 原生HTML 或 Vue 3 + Vite
- **数据库**: SQLite
