from src.agent.Tools.tool import tool_list

intend_map = {
    "agent_tools": {
        "description": "用户需要使用工具完成明确任务，可能需要多步工具调用和推理。",
        "example": "北京天气怎么样？帮我计算 2+3*4。今天 weather 如何？写首诗",
        "tools": tool_list,
    },
    "query_knowledge": {
        "description": "用户需要查询知识库获取相关信息。",
        "example": "LangChain 的核心组件有哪些？什么时候放假，规定是什么？ 我是王刚，检索 部门季度汇报。",
    },
    "emotion_chat": {
        "description": "用户需要情感交流、倾诉或情绪疏导。",
        "example": "我最近很压力，想和你聊聊。你是不是傻。我今天心情不好。",
    },
    "feishu_task": {
        "description": "用户需要飞书任务相关功能，包括定时发送消息、预定会议、记录会议纪要。",
        "example": "帮我定个明天上午10点的会议。提醒我下午3点发消息到群里。记录一下今天的会议内容。",
    },
}
