import os

import dotenv
import yaml
dotenv.load_dotenv()
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.agents import AgentExecutor, create_tool_calling_agent


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

llm = ChatOpenAI(model=config["local_model_name"], temperature=config["local_model_temperature"], base_url=config["local_model_url"], api_key="not-needed")

@tool
def get_current_weather(city: str) -> str:
    """获取指定城市的当前天气信息。当用户询问天气时使用此工具。"""
    # 实际应用中，这里会调用真实的天气 API
    weather_data = {
        "北京": "晴天，气温 28°C，湿度 45%",
        "上海": "多云，气温 25°C，湿度 70%",
        "深圳": "雷阵雨，气温 30°C，湿度 85%",
    }
    return weather_data.get(city, f"抱歉，暂无 {city} 的天气数据")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。当用户需要进行数学计算时使用此工具。
    支持基本的四则运算，如 '2 + 3 * 4'。"""
    import ast
    import operator
   
    # 安全的运算符映射
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
   
    def safe_eval(node):
        if isinstance(node, ast.Expression):
            return safe_eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            return ops[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = safe_eval(node.operand)
            return ops[type(node.op)](operand)
        else:
            raise ValueError(f"不支持的表达式类型: {type(node)}")
   
    try:
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"

@tool
def search_knowledge(query: str) -> str:
    """搜索知识库获取相关信息。当用户询问事实性问题时使用此工具。"""
    # 实际应用中，这里会连接向量数据库或搜索引擎
    knowledge = {
        "LangChain": "LangChain 是一个用于构建 LLM 应用的开源框架，支持链式调用、记忆管理和工具集成。",
        "Python": "Python 是一种高级编程语言，以简洁易读著称，广泛用于 AI、数据科学等领域。",
    }
    for key, value in knowledge.items():
        if key.lower() in query.lower():
            return value
    return f"未找到与 '{query}' 相关的信息"


tools = [get_current_weather, calculate, search_knowledge]

promt = ChatPromptTemplate.from_messages([
    ("system", "你是一个功能强大的 AI 助手，可以使用工具来帮助用户。根据用户的问题，判断是否需要使用工具，选择最合适的工具来获取信息。"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent  = create_tool_calling_agent(llm, tools, promt)


agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


print("=" * 50)
response = agent_executor.invoke({"input": "北京今天天气怎么样？"})
print(f"\n最终回答: {response['output']}")

# 测试 2：数学计算
print("\n" + "=" * 50)
response = agent_executor.invoke({"input": "帮我算一下 (15 * 37 + 228) / 3 等于多少"})
print(f"\n最终回答: {response['output']}")

# 测试 3：综合问题（Agent 需要自己判断用哪个工具）
print("\n" + "=" * 50)
response = agent_executor.invoke({"input": "LangChain 是什么？另外帮我算下 2 的 10 次方"})
print(f"\n最终回答: {response['output']}")





