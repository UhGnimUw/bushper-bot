"""LangGraph-based agent with main agent (intent classification + planning) and sub-agents as nodes.

Main Agent (root node):
  - NLU: classify intent
  - Planning: route to sub-agent nodes
  - Progress tracking

Sub-Agent Nodes:
  - react_node: multi-step tool use (ReAct pattern)
  - rag_node: knowledge base query with tier permission
  - emo_node: emotional chat
  - feishu_task_node: Feishu scheduled messages, meetings, meeting notes
"""
import sys
from pathlib import Path

_agent_dir = Path(__file__).parent
sys.path.insert(0, str(_agent_dir))

from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field

from src.agent.llm import base_llm
from src.agent.intend import intend_map
from src.agent.agmem import get_session_history, get_checkpointer
from src.agent.skill_manager import build_skill_context_for_prompt


# --------------------------------------------------------------------------- #
# Shared state
# --------------------------------------------------------------------------- #

class AgentState(BaseModel):
    messages: list = Field(default_factory=list)
    intent: str = ""
    plan: str = ""
    progress: str = ""
    result: str = ""
    step: str = "nlu"
    needs_human_input: bool = False
    verification_result: str = ""


# --------------------------------------------------------------------------- #
# Intent classification node
# --------------------------------------------------------------------------- #

def nlu_node(state: AgentState) -> AgentState:
    """Classify user intent with keyword pre-check + LLM classification."""
    user_input = _last_user_input(state)
    if not user_input:
        return state

    # Keyword-based fast path for obvious cases
    greeting_keywords = ["你好", "您好", "hi", "hello", "嗨", "嘿", "你好呀"]
    casual_keywords = ["你是谁", "你是机器人吗", "你是什麼", "你是啥", "今天怎么样", "今天咋样", "最近如何"]
    greeting_found = any(kw in user_input for kw in greeting_keywords)
    casual_found = any(kw in user_input for kw in casual_keywords)

    if greeting_found and casual_found:
        intent = "emotion_chat"
    elif greeting_found or casual_found:
        intent = "emotion_chat"
    else:
        # Use LLM for non-obvious cases
        prompt = [
            SystemMessage(content=(
                "你是一个意图分类专家。请根据用户输入，从以下意图中选择一个最合适的。\n\n"
                f"可用意图：{list(intend_map.keys())}\n\n"
                "每个意图的定义：\n"
                + "\n".join(f"- {k}: {v['description']}" for k, v in intend_map.items())
                + "\n\n"
                "判断规则：\n"
                "1. 【打招呼/问候/闲聊】→ emotion_chat：'你好'、'您好'、'你是谁'、'今天怎么样'、'最近如何'、'你好呀'\n"
                "2. 【情感倾诉/情绪表达】→ emotion_chat：'我心情不好'、'我很压力'、'我最近很沮丧'、'和我聊聊'\n"
                "3. 【知识库查询】→ query_knowledge：用户必须同时提供姓名 AND 查询请求，如'我是张三，检索xxx'、'我是李四，查一下xxx'\n"
                "4. 【工具任务】→ agent_tools：'天气'、'计算'、'搜索'、'股价'、'帮我做xxx'\n"
                "5. 【飞书任务】→ feishu_task：'定会议'、'发消息'、'记录会议'、'提醒我'\n\n"
                "只输出意图名称，不要解释。"
            )),
            HumanMessage(content=f"用户输入：{user_input}"),
        ]

        class IntentOut(BaseModel):
            intent: str = Field(description="意图名称")

        result = base_llm.with_structured_output(IntentOut).invoke(prompt)
        intent = result.intent

    return AgentState(
        messages=state.messages,
        intent=intent,
        plan="",
        progress="[NLU] 已完成意图识别：" + intent,
        step="nlu",
    )


# --------------------------------------------------------------------------- #
# Planning node
# --------------------------------------------------------------------------- #

def plan_node(state: AgentState) -> AgentState:
    """Generate execution plan for the classified intent."""
    intent = state.intent

    plan_map = {
        "agent_tools": "需要多步工具调用来完成任务，我将分析问题、选择工具、执行操作并返回结果。",
        "query_knowledge": "将在知识库中检索相关信息，根据用户权限层级返回对应范围的答案。",
        "emotion_chat": "以共情的方式与用户交流，提供情感支持和倾听。",
        "feishu_task": "调用飞书任务API完成：定时消息/预定会议/记录会议纪要。",
    }

    plan = plan_map.get(intent, "未知意图，无法处理。")
    return AgentState(
        messages=state.messages,
        intent=intent,
        plan=plan,
        progress="[规划] " + plan,
        step="plan",
    )


# --------------------------------------------------------------------------- #
# Route function
# --------------------------------------------------------------------------- #

def route_by_intent(state: AgentState) -> Literal["react_node", "rag_node", "emo_node", "feishu_task_node"]:
    """Route to appropriate sub-agent based on intent."""
    intent_router = {
        "agent_tools": "react_node",
        "query_knowledge": "rag_node",
        "emotion_chat": "emo_node",
        "feishu_task": "feishu_task_node",
    }
    return intent_router.get(state.intent, END)


# --------------------------------------------------------------------------- #
# Verification node — validate sub-agent result
# --------------------------------------------------------------------------- #

def verify_node(state: AgentState) -> AgentState:
    """Verify sub-agent result: if incomplete/conflicting, request human input or replan."""
    sub_result = state.result
    intent = state.intent
    user_input = _last_user_input(state)

    verify_prompt = [
        SystemMessage(content=(
            "你是一个结果验证专家。验证子Agent的返回结果是否满足用户需求。\n\n"
            "验证维度：\n"
            "1. 完整性 — 是否解决了用户的问题\n"
            "2. 准确性 — 结果是否符合常识和业务逻辑\n"
            "3. 需求匹配 — 是否匹配了用户的原始意图\n\n"
            "如果结果满足要求，返回 PASS。\n"
            "如果需要用户补充信息（如缺少参数：时间、地点、人名等），返回 NEED_MORE_INFO 并说明需要什么。\n"
            "如果结果明显错误，返回 FAIL 并说明原因。\n\n"
            "输出格式：\n"
            "VERIFICATION: PASS | NEED_MORE_INFO | FAIL\n"
            "REASON: <原因或说明>\n"
            "如果 NEED_MORE_INFO，附加：NEED_INFO: <需要补充的信息描述>"
        )),
        HumanMessage(content=(
            f"用户原始输入：{user_input}\n"
            f"意图类型：{intent}\n"
            f"子Agent返回结果：{sub_result}\n\n"
            "请验证："
        )),
    ]

    class VerifyOut(BaseModel):
        verification: str = Field(description="验证结果: PASS | NEED_MORE_INFO | FAIL")
        reason: str = Field(description="原因或说明")
        need_info: str = Field(default="", description="如果 NEED_MORE_INFO，描述需要补充的信息")

    raw = base_llm.with_structured_output(VerifyOut).invoke(verify_prompt)

    if raw.verification == "PASS":
        return AgentState(
            messages=state.messages,
            intent=state.intent,
            plan=state.plan,
            progress=state.progress + f"\n[验证] 通过 — {raw.reason}",
            result=state.result,
            step="verify",
            needs_human_input=False,
            verification_result=f"验证通过：{raw.reason}",
        )
    elif raw.verification == "NEED_MORE_INFO":
        return AgentState(
            messages=state.messages,
            intent=state.intent,
            plan=state.plan,
            progress=state.progress + f"\n[验证] 需要补充信息 — {raw.need_info}",
            result=f"我需要您补充一些信息：{raw.need_info}",
            step="verify",
            needs_human_input=True,
            verification_result=f"需要补充信息：{raw.need_info}",
        )
    else:  # FAIL
        return AgentState(
            messages=state.messages,
            intent=state.intent,
            plan=state.plan,
            progress=state.progress + f"\n[验证] 失败 — {raw.reason}，将重新规划",
            result="",
            step="verify",
            needs_human_input=False,
            verification_result=f"验证失败：{raw.reason}",
        )


# --------------------------------------------------------------------------- #
# Human input node — wait for user to provide missing info
# --------------------------------------------------------------------------- #

def human_input_node(state: AgentState) -> AgentState:
    """Present clarification question to user and wait for response.

    Appends an AIMessage with the clarification prompt to state.messages
    so the frontend can display it immediately.
    """
    clarification = (
        f"我需要您补充一些信息：{state.verification_result.replace('需要补充信息：', '')}\n"
        "请回复您要补充的具体内容。"
    )
    new_messages = list(state.messages) + [AIMessage(content=clarification)]
    return AgentState(
        messages=new_messages,
        intent=state.intent,
        plan=state.plan,
        progress=state.progress + "\n[人类介入] 等待用户补充信息...",
        result=clarification,
        step="human_input",
        needs_human_input=True,
        verification_result=state.verification_result,
    )


# --------------------------------------------------------------------------- #
# Route: after verify, decide next step
# --------------------------------------------------------------------------- #

def route_after_verify(state: AgentState) -> str:
    """After verification: FAIL -> replan; NEED_MORE_INFO -> human_input; PASS -> end_node."""
    if state.verification_result.startswith("验证失败") and not state.result:
        return "plan"
    if state.needs_human_input:
        return "human_input"
    return "end_node"


# --------------------------------------------------------------------------- #
# Sub-agent nodes
# --------------------------------------------------------------------------- #

def react_node(state: AgentState) -> AgentState:
    """ReAct sub-agent — multi-step tool calling."""
    from src.agent.agent_react import ReActAgent
    user_input = _last_user_input(state)

    react = ReActAgent()
    result = react.invoke(user_input, session_id=_session_id(state))

    return AgentState(
        messages=state.messages,
        intent=state.intent,
        plan=state.plan,
        progress="[ReAct] 已完成工具调用",
        result=result,
        step="react",
        needs_human_input=False,
        verification_result="",
    )


def rag_node(state: AgentState) -> AgentState:
    """RAG sub-agent — knowledge base query with tier permission."""
    from src.agent.agent_rag import RAGAgent
    user_input = _last_user_input(state)

    rag = RAGAgent()
    result = rag.invoke(user_input, session_id=_session_id(state))

    return AgentState(
        messages=state.messages,
        intent=state.intent,
        plan=state.plan,
        progress="[RAG] 已完成知识检索",
        result=result,
        step="rag",
        needs_human_input=False,
        verification_result="",
    )


def emo_node(state: AgentState) -> AgentState:
    """Emotional chat sub-agent."""
    from src.agent.agent_emo import EmoAgent
    user_input = _last_user_input(state)

    emo = EmoAgent()
    result = emo.invoke(user_input, session_id=_session_id(state))

    return AgentState(
        messages=state.messages,
        intent=state.intent,
        plan=state.plan,
        progress="[Emo] 已完成情感交流",
        result=result,
        step="emo",
        needs_human_input=False,
        verification_result="",
    )


def feishu_task_node(state: AgentState) -> AgentState:
    """Feishu task sub-agent — scheduled messages, meetings, meeting notes."""
    from src.agent.agent_feishu_task import FeishuTaskAgent
    user_input = _last_user_input(state)

    feishu = FeishuTaskAgent()
    result = feishu.invoke(user_input, session_id=_session_id(state))

    return AgentState(
        messages=state.messages,
        intent=state.intent,
        plan=state.plan,
        progress="[Feishu] 已完成任务",
        result=result,
        step="feishu",
        needs_human_input=False,
        verification_result="",
    )


# --------------------------------------------------------------------------- #
# Build graph
# --------------------------------------------------------------------------- #

def _build_graph():
    """Build and return the LangGraph agent."""
    builder = StateGraph(AgentState)

    builder.add_node("nlu", nlu_node)
    builder.add_node("plan", plan_node)
    builder.add_node("verify", verify_node)
    builder.add_node("human_input", human_input_node)
    builder.add_node("react_node", react_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("emo_node", emo_node)
    builder.add_node("feishu_task_node", feishu_task_node)
    builder.add_node("end_node", lambda s: s)   # explicit end node

    # Main flow: NLU → Plan → Sub-agent → Verify → (END or Replan)
    builder.set_entry_point("nlu")
    builder.add_edge("nlu", "plan")
    builder.add_conditional_edges("plan", route_by_intent)

    # Sub-agents → Verify
    for node in ["react_node", "rag_node", "emo_node", "feishu_task_node"]:
        builder.add_edge(node, "verify")

    # Verify → (plan | human_input | end_node)
    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {"plan": "plan", "human_input": "human_input", "end_node": "end_node"},
    )
    builder.add_edge("human_input", "end_node")

    return builder.compile(checkpointer=get_checkpointer())


_langgraph_agent = None


def get_langgraph_agent():
    global _langgraph_agent
    if _langgraph_agent is None:
        _langgraph_agent = _build_graph()
    return _langgraph_agent


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _last_user_input(state: AgentState) -> str:
    for msg in reversed(state.messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


def _session_id(state: AgentState) -> str:
    import hashlib
    msg_text = "".join(m.content for m in state.messages[:1])
    if msg_text:
        return hashlib.md5(msg_text.encode()).hexdigest()[:8]
    return "default"


# --------------------------------------------------------------------------- #
# Main entry
# --------------------------------------------------------------------------- #

def invoke(user_input: str, session_id: str = "default"):
    """Main entry point for the LangGraph agent.

    Returns:
        tuple[str, bool]: (response_text, needs_human_input)
    """
    agent = get_langgraph_agent()

    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={
            "configurable": {
                "session_id": session_id,
                "thread_id": session_id,
            }
        },
    )

    # result is a dict with full state after all nodes complete
    needs_human_input = False
    text = ""

    if isinstance(result, dict):
        needs_human_input = result.get("needs_human_input", False)
        # AgentState.result takes priority — it's the sub-agent's answer
        state_result = result.get("result", "")
        if state_result:
            text = state_result
        else:
            # Fallback: get last AI message
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    text = msg.content
                    break

    print(f"[invoke DEBUG] needs_human_input={needs_human_input}, text={text[:50] if text else '(empty)'}")
    return text, needs_human_input


if __name__ == "__main__":
    print("Testing LangGraph agent...")

    test_inputs = [
        "北京天气怎么样？",
        "LangChain的核心组件有哪些？",
        "我最近心情不好，想聊聊",
        "帮我定个明天上午10点的会议",
    ]

    for inp in test_inputs:
        print(f"\n>>> {inp}")
        print(invoke(inp))