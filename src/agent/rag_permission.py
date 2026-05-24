"""RAG permission — ToolNode 执行 get_user_tier tool，返回真实 tier。

resolve_tier_from_prompt：
  prompt → LLM 生成 tool_call → ToolNode 执行 → 返回带 tier 的结果
"""
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import create_agent
from langchain_core.tools import Tool

from src.agent.llm import base_llm
from src.agent.Tools.tool import get_user_tier

logger = logging.getLogger(__name__)


def resolve_tier_from_prompt(prompt: str) -> tuple[str, str]:
    """LLM 提取用户名 → ToolNode 执行 get_user_tier → 返回 (user_name, tier)。"""
    try:
        messages = [
            SystemMessage(content="你是一个智能助手。必须从用户输入中提取'user_name'参数并调用get_user_tier工具。"),
            HumanMessage(content=prompt),
        ]

        # LLM 生成 tool call
        result = base_llm.bind_tools([get_user_tier]).invoke(messages)

        tool_calls = getattr(result, "tool_calls", [])
        if not tool_calls:
            logger.warning("[resolve_tier] no tool_call generated, content=%s", result.content)
            return "未知用户", "T3"

        # 找到 get_user_tier 的调用参数
        user_name = None
        for tc in tool_calls:
            if tc.get("name") == "get_user_tier":
                user_name = tc.get("args", {}).get("user_name")

        if not user_name:
            logger.warning("[resolve_tier] user_name not extracted")
            return "未知用户", "T3"

        # 直接调用 tool 函数获取 tier（不走 LLM 解析返回值）
        tier_raw = get_user_tier.invoke(user_name)
        logger.info("[resolve_tier] get_user_tier(%s) = %s", user_name, tier_raw)

        # 解析返回：可能是 "T0"/"T1"/"T2"/"T3" 或 "未找到用户"
        tier = tier_raw.strip() if isinstance(tier_raw, str) else "T3"
        if tier not in ("T0", "T1", "T2", "T3"):
            tier = "T3"

        return user_name, tier

    except Exception as e:
        logger.error("[resolve_tier] exception: %s", e)
        return "未知用户", "T3"
