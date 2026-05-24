# Graph Report - /mnt/e/test/proj/myagent  (2026-05-04)

## Corpus Check
- Corpus is ~2,837 words - fits in a single context window. You may not need a graph.

## Summary
- 103 nodes · 95 edges · 17 communities detected
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Agent Orchestration|Agent Orchestration]]
- [[_COMMUNITY_Tool Definitions|Tool Definitions]]
- [[_COMMUNITY_Feishu Bot|Feishu Bot]]
- [[_COMMUNITY_Agent Core|Agent Core]]
- [[_COMMUNITY_DingTalk Bot|DingTalk Bot]]
- [[_COMMUNITY_Embeddings|Embeddings]]
- [[_COMMUNITY_Reference Implementations|Reference Implementations]]
- [[_COMMUNITY_Test Mocks|Test Mocks]]
- [[_COMMUNITY_RAG Agent|RAG Agent]]
- [[_COMMUNITY_ReAct Agent|ReAct Agent]]
- [[_COMMUNITY_Memory|Memory]]
- [[_COMMUNITY_Weather Tools|Weather Tools]]
- [[_COMMUNITY_Message Processing|Message Processing]]
- [[_COMMUNITY_API Clients|API Clients]]
- [[_COMMUNITY_Test Infrastructure|Test Infrastructure]]
- [[_COMMUNITY_Utility Functions|Utility Functions]]
- [[_COMMUNITY_Configuration|Configuration]]

## God Nodes (most connected - your core abstractions)
1. `Intent Mapping Configuration` - 6 edges
2. `CustomEmbeddings` - 5 edges
3. `Agent Router` - 5 edges
4. `LangChainBotHandler` - 4 edges
5. `main()` - 4 edges
6. `get_agent()` - 4 edges
7. `RAGAgent` - 4 edges
8. `MockLarkClient` - 4 edges
9. `RAG Agent` - 4 edges
10. `ReAct Agent` - 4 edges

## Surprising Connections (you probably didn't know these)
- `agent_response()` --calls--> `get_agent()`  [INFERRED]
  feishu.py → src/agent/agent.py
- `RAG Agent` --semantically_similar_to--> `RAG Reference Implementation`  [INFERRED] [semantically similar]
  /mnt/e/test/proj/myagent/src/agent/agent_rag.py → /mnt/e/test/proj/myagent/reference/rag.py
- `ReAct Agent` --semantically_similar_to--> `ReAct Reference Implementation`  [INFERRED] [semantically similar]
  /mnt/e/test/proj/myagent/src/agent/agent_react.py → /mnt/e/test/proj/myagent/reference/react.py
- `Agent Memory Singleton` --semantically_similar_to--> `Session Memory Reference`  [INFERRED] [semantically similar]
  /mnt/e/test/proj/myagent/src/agent/agmem.py → /mnt/e/test/proj/myagent/reference/memory.py
- `Agent Router` --routes_to--> `Tool Agent`  [EXTRACTED]
  /mnt/e/test/proj/myagent/src/agent/agent.py → /mnt/e/test/proj/myagent/src/agent/agent_tools.py

## Hyperedges (group relationships)
- **Tool-Based Agent Implementation** — agent_py_get_agent, intend_user_tools, agent_react_py_reactagent, agent_tools_py_toolagent [EXTRACTED 0.95]
- **Intent Routing System** — agent_py_nlu, agent_py_intendforecast, intend_py_intend_map, intend_user_tools, intend_quary_knowledge, intend_agetn_react, intend_emotion_chat [EXTRACTED 0.95]
- **LLM Configuration System** — llm_py_base_llm, llm_py_advanced_llm, llm_py_embedding_model [EXTRACTED 0.95]

## Communities (25 total, 10 thin omitted)

### Community 0 - "Agent Orchestration"
Cohesion: 0.14
Nodes (17): Agent Router, Intent Forecast Model, Natural Language Understanding, RAG Agent, ReAct Agent, Tool Agent, Agent ReAct Intent, Emotion Chat Intent (+9 more)

### Community 1 - "Tool Definitions"
Cohesion: 0.18
Nodes (10): calculate(), get_current_weather(), get_stock_price(), 搜索知识库获取相关信息。当用户询问事实性问题时使用此工具。, 搜索指定公司的财经新闻      Args:         company: 公司名称     Return:         公司的财经新闻，每个新闻占一行, 获取指定公司的股票价格信息      Args:         company: 公司名称（如：苹果公司, 微软公司, 谷歌公司）         timef, 获取指定城市的当前天气信息。当用户询问天气时使用此工具。, 计算数学表达式。当用户需要进行数学计算时使用此工具。 (+2 more)

### Community 2 - "Feishu Bot"
Cohesion: 0.27
Nodes (9): DingTalk Stream Bot, LangChain Bot Handler, Feishu Message Handler, Processed Messages Deque, agent_response(), define_options(), do_p2_im_message_receive_v1(), main() (+1 more)

### Community 3 - "Agent Core"
Cohesion: 0.25
Nodes (5): get_agent(), IntendForecast, NLU(), ToolAgent, BaseModel

### Community 4 - "DingTalk Bot"
Cohesion: 0.36
Nodes (4): define_options(), LangChainBotHandler, main(), setup_logger()

### Community 6 - "Reference Implementations"
Cohesion: 0.29
Nodes (6): calculate(), get_current_weather(), 获取指定城市的当前天气信息。当用户询问天气时使用此工具。, 计算数学表达式。当用户需要进行数学计算时使用此工具。     支持基本的四则运算，如 '2 + 3 * 4'。, 搜索知识库获取相关信息。当用户询问事实性问题时使用此工具。, search_knowledge()

### Community 7 - "Test Mocks"
Cohesion: 0.38
Nodes (3): main(), MockLarkClient, MockP2ImMessageReceiveV1

## Knowledge Gaps
- **25 isolated node(s):** `获取指定城市的当前天气信息。当用户询问天气时使用此工具。`, `计算数学表达式。当用户需要进行数学计算时使用此工具。     支持基本的四则运算，如 '2 + 3 * 4'。`, `搜索知识库获取相关信息。当用户询问事实性问题时使用此工具。`, `获取指定公司的股票价格信息      Args:         company: 公司名称（如：苹果公司, 微软公司, 谷歌公司）         timef`, `搜索指定公司的财经新闻      Args:         company: 公司名称     Return:         公司的财经新闻，每个新闻占一行` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Agent Router` connect `Agent Orchestration` to `Feishu Bot`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `agent_response()` connect `Feishu Bot` to `Agent Core`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `get_agent()` connect `Agent Core` to `Feishu Bot`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **What connects `获取指定城市的当前天气信息。当用户询问天气时使用此工具。`, `计算数学表达式。当用户需要进行数学计算时使用此工具。     支持基本的四则运算，如 '2 + 3 * 4'。`, `搜索知识库获取相关信息。当用户询问事实性问题时使用此工具。` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Agent Orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._