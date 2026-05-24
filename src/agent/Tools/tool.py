import yaml
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool
import os
import time
import json

load_dotenv()


@tool
def execute_sql(query: str) -> str:
    """执行 SQL 查询并返回结果（仅支持 SELECT，禁止增删改）。

    Args:
        query: SELECT 语句，支持 WHERE 条件筛选。
              表结构：
                - department(id, name, description)
                - people(id, dept_id, name, gender, age, phone, description)
              通过 description 字段可以查询人员。
    """
    import sqlite3

    q = query.strip().lower()
    if not q.startswith("select"):
        return "只允许 SELECT 查询，禁止增删改操作。"

    db_path = Path(__file__).parent.parent.parent.parent / "data.db"
    if not db_path.exists():
        return f"数据库文件不存在：{db_path}"

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query.strip())

        if cur.description is None:
            return "查询成功，无返回数据。"

        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "查询成功，无匹配记录。"

        MAX_ROWS = 50
        rows = rows[:MAX_ROWS]
        lines = [", ".join(f"{c}={v!r}" for c, v in zip(cols, row)) for row in rows]
        result = "\n".join(lines)
        if len(rows) == MAX_ROWS:
            result += f"\n(... 共 {MAX_ROWS} 条，已截断)"
        else:
            result = f"共 {len(rows)} 条记录：\n" + result
        return result
    except sqlite3.OperationalError as e:
        return f"数据库连接失败：{e}"
    except sqlite3.ProgrammingError as e:
        return f"SQL 执行错误：{e}"
    except Exception as e:
        return f"执行出错：{e}"


@tool
def search_people(query: str) -> str:
    """搜索人员信息 — 仅在用户明确表示找人时使用。

    触发场景（满足任一）：
    - 用户提到"谁"、"找谁"、"负责人是谁"、"谁负责"
    - 用户不知道具体姓名，用职责/部门等关键词找人
    - 用户说"前端开发是谁"、"数据分析找谁"

    禁止触发：
    - 用户已给出具体姓名（如"王刚"）
    - 用户只是问天气、新闻等无关内容

    Args:
        query: 职责描述关键词，如"前端开发"、"数据分析"、"运维"等。
    """
    import sqlite3

    sql = (
        "SELECT p.id, p.name, p.gender, p.age, p.phone, "
        "p.description, d.name as department "
        "FROM people p "
        "LEFT JOIN department d ON p.dept_id = d.id "
        "WHERE p.description LIKE ? "
        "LIMIT 20"
    )
    try:
        db_path = Path(__file__).parent.parent.parent.parent / "data.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, (f"%{query}%",))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return f"未找到职责描述包含「{query}」的人员。"

        lines = []
        for row in rows:
            dept = row[6] or "未分配"
            lines.append(
                f"姓名：{row[1]}，部门：{dept}，性别：{row[2]}，"
                f"年龄：{row[3]}，电话：{row[4]}，职责：{row[5]}"
            )
        return "共 {} 条记录：\n{}".format(len(rows), "\n".join(lines))
    except Exception as e:
        return f"查询出错：{e}"


@tool
def get_user_tier(user_name: str) -> str:
    """根据用户姓名查询其权限层级。

    Args:
        user_name: 用户姓名。
    Returns:
        权限层级字符串（T0/T1/T2/T3）或"未找到用户"。

    注意：调用此工具前，需要从用户提示词中识别出用户姓名。
    """
    import sqlite3
    from pathlib import Path

    if not user_name or not user_name.strip():
        return "未提供用户名"

    db_path = Path(__file__).parent.parent.parent.parent / "data.db"
    if not db_path.exists():
        return f"数据库文件不存在：{db_path}"

    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.execute(
            "SELECT tier FROM user_permission WHERE user_name = ?",
            (user_name.strip(),)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0]
        return "未找到用户"
    except Exception as e:
        return f"查询出错：{e}"


@tool
def get_department_list() -> str:
    """获取所有部门列表及其描述。"""
    import sqlite3

    sql = "SELECT name, description FROM department ORDER BY id"
    try:
        db_path = Path(__file__).parent.parent.parent.parent / "data.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "暂无部门数据。"
        lines = [f"{row[0]}：{row[1]}" for row in rows]
        return "共 {} 个部门：\n{}".format(len(rows), "\n".join(lines))
    except Exception as e:
        return f"查询出错：{e}"


# =============================================================================
# 以下为原有工具（保持不变）
# =============================================================================

@tool
def get_stock_price(company: str, timeframe: str = "today") -> str:
    """获取指定公司的股票价格信息

    Args:
        company: 公司名称（如：苹果公司, 微软公司, 谷歌公司）
        timeframe: 时间范围（today-今日, week-本周, month-本月）
    """
    mock_data = {
        "苹果公司": {"today": 185.20, "week": 183.50, "month": 180.75},
        "微软公司": {"today": 415.86, "week": 412.30, "month": 405.42},
        "谷歌公司": {"today": 15.42, "week": 15.20, "month": 14.85}
    }

    if company in mock_data:
        price = mock_data[company].get(timeframe, "未知时间范围")
        return f"{company} {timeframe}价格: {price}美元"
    else:
        return f"未找到股票代码 {company} 的数据"


@tool
def search_news(company: str) -> str:
    """搜索指定公司的财经新闻

    Args:
        company: 公司名称
    Return:
        公司的财经新闻，每个新闻占一行
    """
    mock_news = {
        "苹果公司": [
            "苹果发布新款iPhone，股价上涨3%",
            "苹果与欧盟达成反垄断和解协议",
            "苹果将在印度扩大生产规模"
        ],
        "微软公司": [
            "微软Azure云业务季度增长超预期",
            "微软完成对Nuance的收购",
            "微软推出新一代AI助手Copilot"
        ],
        "谷歌公司": [
            "谷歌发布新AI模型，性能提升20%",
            "谷歌与OpenAI合作，开发新的AI助手",
            "谷歌在欧洲展开AI研究项目"
        ]
    }

    news_list = mock_news.get(company, [f"未找到{company}的相关新闻"])
    return "\n".join(news_list)

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

local_llm = ChatOpenAI(
    model_name="qwen3.5",
    temperature=0.1,
    base_url="http://127.0.0.1:8989/v1",
    api_key="sk-",
)

class WeatherQuery(BaseModel):
    loc: str = Field(description="城市名称")

@tool(args_schema=WeatherQuery)
def get_current_weather(loc):
    """
        查询即时天气函数
        :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
        :return：心知天气 API查询即时天气的结果，具体URL请求地址为："https://api.seniverse.com/v3/weather/now.json"
        返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
    """
    url = "https://api.seniverse.com/v3/weather/now.json"
    params = {
        "key": "SoBfZtwFHKtFLIp7y",
        "location": loc,
        "language": "zh-Hans",
        "unit": "c",
    }
    response = requests.get(url, params=params)
    temperature = response.json()
    return temperature['results'][0]['now']



@tool
def calculate(expression: str) -> str:
    """计算数学表达式。当用户需要进行数学计算时使用此工具。"""
    import ast
    import operator

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

from langchain_tavily import TavilySearch

# 全局初始化搜索工具，避免重复创建
_tavily_search = None

def _get_search_tool():
    """获取或初始化 Tavily 搜索工具"""
    global _tavily_search
    if _tavily_search is None:
        api_key = os.getenv("TAVILY_API_KEY", "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")
        _tavily_search = TavilySearch(
            max_results=3,
            topic="general",
            tavily_api_key=api_key
        )
    return _tavily_search

@tool
def search_web(query: str) -> str:
    """搜索互联网获取最新信息。当用户询问实时新闻、最新消息或网上才能找到的信息时使用此工具。
    
    Args:
        query: 搜索关键词，越具体越好
    """
    try:
        search_tool = _get_search_tool()
        results = search_tool.invoke(query)
        
        if hasattr(results, 'content') and results.content:
            return f"搜索结果：\n{results.content}"
        
        if isinstance(results, list) and len(results) > 0:
            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get('title', f"结果 {i}")
                content = result.get('content', result.get('text', ''))
                url = result.get('url', '')
                formatted.append(f"[{i}] {title}\n{content}\n来源: {url}\n")
            return "搜索结果：\n\n" + "\n---\n".join(formatted)
        
        return f"搜索结果：{str(results)}"
        
    except Exception as e:
        return f"搜索失败：{str(e)}"







@tool
def convert_words_to_poetry(words: str, style: str = "古诗", poetry_format: str = "五言绝句") -> str:
    """将用户提供的单词或关键词转换为诗词。

    当用户请求写诗、作诗、将单词转换为诗词时使用此工具。

    Args:
        words: 要转换为诗词的核心词/关键词（必填），如"秋风"、"离别"、"明月"
        style: 诗词风格（选填），可选值：古诗、现代诗、抒情诗、豪放派、婉约派，默认为"古诗"
        poetry_format: 格式（选填），可选值：五言绝句、七言绝句、五言律诗、七言律诗、词牌名（如沁园春、清平乐），默认为"五言绝句"
    """
    from src.agent.llm import advanced_llm

    prompt = f"""你是一位精通中国古典诗词的大师。请根据用户提供的关键词，创作一首符合要求的诗词。

要求：
- 必须严格包含用户提供的核心关键词
- 风格：{style}
- 格式：{poetry_format}
- 诗词要有意境和韵味

用户提供的关键词：{words}

请直接输出诗词作品，不要解释过程。"""

    try:
        result = advanced_llm.invoke(prompt)
        return result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        return f"诗词生成失败：{e}"


tool_list = [
    execute_sql,
    search_people,
    get_department_list,
    get_current_weather,
    calculate,
    get_stock_price,
    search_news,
    search_web,
]


# =============================================================================
# 飞书任务工具
# =============================================================================


def _get_lark_client():
    """Get Feishu client instance."""
    import lark_oapi as lark
    return lark.Client.builder() \
        .app_id(os.getenv("FEISHU_APP_ID", "cli_a97d8246ff38dcd2")) \
        .app_secret(os.getenv("FEISHU_APP_SECRET", "h8vsRaBgt8AvSF8ndvEQsgv5Ly5yl7dl")) \
        .domain(lark.FEISHU_DOMAIN) \
        .log_level(lark.LogLevel.INFO) \
        .build()


@tool
def schedule_message(chat_id: str, content: str, send_timestamp: int) -> str:
    """定时发送消息到飞书群组。

    当用户请求在特定时间发送消息到群组时使用此工具。
    使用飞书原生API的schedule_time参数实现定时发送。

    Args:
        chat_id: 群组ID，用于接收消息的群
        content: 要发送的消息内容
        send_timestamp: 发送时间的Unix时间戳（秒），例如 int(time.time()) + 600 表示10分钟后发送
    """
    try:
        from datetime import datetime
        import lark_oapi as lark
        from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

        client = _get_lark_client()

        body = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": content}, ensure_ascii=False))
                .schedule_time(send_timestamp)
                .build()
            ) \
            .build()

        response = client.im.v1.message.create(body)

        if response.success():
            msg_id = response.data.message_id if response.data else None
            send_time_str = datetime.fromtimestamp(send_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            return f"定时消息已设置成功！\n群组ID：{chat_id}\n发送时间：{send_time_str}\n消息ID：{msg_id}"
        return f"设置定时消息失败：{response.msg}"
    except Exception as e:
        return f"设置定时消息失败：{str(e)}"


@tool
def create_meeting(title: str, start_time: str, end_time: str, description: str = "", attendee_emails: str = "", location: str = "") -> str:
    """预定飞书会议。

    当用户请求创建会议或日程时使用此工具。

    Args:
        title: 会议标题/主题
        start_time: 会议开始时间，格式为 "YYYY-MM-DD HH:MM:SS"，例如 "2026-05-20 10:00:00"
        end_time: 会议结束时间，格式为 "YYYY-MM-DD HH:MM:SS"，例如 "2026-05-20 11:00:00"
        description: 会议描述/议程（可选）
        attendee_emails: 参会人邮箱，多个用逗号分隔（可选），例如 "user1@company.com,user2@company.com"
        location: 会议地点（可选）
    """
    try:
        from datetime import datetime
        import lark_oapi as lark
        from lark_oapi.api.calendar.v4 import CreateCalendarEventRequest, CalendarEvent, TimeInfo, EventLocation, Reminder

        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        if end_dt <= start_dt:
            return "会议结束时间必须晚于开始时间"

        client = _get_lark_client()

        # 构建时间对象
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        start_time_obj = TimeInfo.builder() \
            .timestamp(str(start_ts)) \
            .timezone("Asia/Shanghai") \
            .build()
        end_time_obj = TimeInfo.builder() \
            .timestamp(str(end_ts)) \
            .timezone("Asia/Shanghai") \
            .build()

        # 构建事件对象
        event_builder = CalendarEvent.builder() \
            .summary(title) \
            .description(description or "") \
            .start_time(start_time_obj) \
            .end_time(end_time_obj) \
            .reminders([Reminder.builder().minutes(15).build()])

        # 添加位置（如果有）
        if location:
            event_builder = event_builder.location(
                EventLocation.builder().name(location).build()
            )

        event = event_builder.build()

        # 构建请求
        request = CreateCalendarEventRequest.builder() \
            .calendar_id("primary") \
            .request_body(event) \
            .build()
        response = client.calendar.v4.calendar_event.create(request)

        if response.success():
            event = response.data.event if response.data else None
            event_id = event.event_id if event else None

            if event_id and attendee_emails:
                _add_meeting_attendees(client, event_id, attendee_emails)

            return f"会议已创建成功！\n标题：{title}\n开始时间：{start_time}\n结束时间：{end_time}\n会议ID：{event_id}"
        return f"创建会议失败：{response.msg}"
    except ValueError:
        return f"时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式"
    except Exception as e:
        return f"预定会议失败：{str(e)}"


def _add_meeting_attendees(client, event_id: str, attendee_emails: str):
    """Add attendees to an existing meeting event."""
    from lark_oapi.api.calendar.v4 import CreateCalendarEventAttendeeRequest, CreateCalendarEventAttendeeRequestBody, CalendarEventAttendee

    emails = [e.strip() for e in attendee_emails.split(",") if e.strip()]
    attendees = [CalendarEventAttendee.builder().type("user").third_party_email(email).build() for email in emails]

    body = CreateCalendarEventAttendeeRequestBody.builder().attendees(attendees).build()
    request = CreateCalendarEventAttendeeRequest.builder() \
        .calendar_id("primary") \
        .event_id(event_id) \
        .request_body(body) \
        .build()
    client.calendar.v4.calendar_event_attendee.create(request)


@tool
def create_meeting_minutes(event_id: str, title: str, content: str) -> str:
    """记录会议纪要。

    注意：当前飞书SDK的创建会议纪要API已更改，此功能可能不可用。
    建议用户直接在飞书中手动记录会议纪要。

    Args:
        event_id: 会议ID（来自create_meeting的返回）
        title: 会议纪要标题
        content: 会议纪要内容，可以包含讨论要点、决策、行动项等
    """
    try:
        # 当前飞书SDK的会议纪要API已经改变，这里我们先返回一个提示
        return (f"注意：飞书SDK更新后，会议纪要功能API已变更。\n"
                f"当前无法通过此工具自动创建会议纪要。\n"
                f"建议您直接在飞书中为会议 {event_id} 手动添加纪要。\n"
                f"标题：{title}\n内容预览：\n{content[:200]}{'...' if len(content) > 200 else ''}")
    except Exception as e:
        return f"记录会议纪要失败: {str(e)}"


task_tool_list = [
    schedule_message,
    create_meeting,
    create_meeting_minutes,
]
