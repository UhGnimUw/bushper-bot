"""飞书任务工具 — 定时消息、会议预定、会议纪要。"""
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# 全局 client lazy init
_client = None

def get_feishu_client():
    """获取或创建飞书客户端。"""
    global _client
    if _client is None:
        import lark_oapi as lark
        import os
        _client = lark.Client.builder() \
            .app_id(os.getenv("FEISHU_APP_ID", "")) \
            .app_secret(os.getenv("FEISHU_APP_SECRET", "")) \
            .domain(lark.FEISHU_DOMAIN) \
            .log_level(lark.LogLevel.INFO) \
            .build()
    return _client


@tool
def schedule_message(receive_id: str, content: str, msg_type: str = "text",
                     schedule_time: int = None, receive_id_type: str = "chat_id") -> str:
    """定时发送消息到飞书群组或用户。

    Args:
        receive_id: 接收方ID（群组ID或用户ID）
        content: 消息内容
        msg_type: 消息类型，默认text
        schedule_time: Unix时间戳（秒），留空则立即发送
        receive_id_type: 接收ID类型，默认chat_id，可选open_id
    """
    client = get_feishu_client()

    if schedule_time is None:
        schedule_time = int(time.time()) + 60  # 默认1分钟后

    body = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": json.dumps({"text": content}, ensure_ascii=False),
        "schedule_time": schedule_time,
    }

    from lark_oapi.api.im.v1 import CreateMessageRequest

    request = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(body) \
        .build()

    response = client.im.v1.message.create(request)

    if response.success():
        data = response.data
        return (f"消息已安排发送！\nmessage_id: {data.message_id}\n"
                f"计划发送时间: {datetime.fromtimestamp(data.schedule_time, tz=timezone(timedelta(hours=8)))}\n状态: {data.status}")
    else:
        return f"发送失败: code={response.code}, msg={response.msg}"


@tool
def create_meeting(summary: str, start_time: int = None, end_time: int = None,
                   description: str = "", attendees: list = None,
                   location: str = "", reminder_minutes: int = 15) -> str:
    """预定飞书会议。

    Args:
        summary: 会议标题
        start_time: Unix时间戳（秒），默认1小时后
        end_time: Unix时间戳（秒），默认2小时后
        description: 会议描述
        attendees: 参与者user_id列表，如["ou_xxx", "ou_yyy"]
        location: 会议地点
        reminder_minutes: 提前多少分钟提醒
    """
    client = get_feishu_client()

    if start_time is None:
        start_time = int(time.time()) + 3600
    if end_time is None:
        end_time = start_time + 3600

    from lark_oapi.api.calendar.v4 import CreateCalendarEventRequest, CalendarEvent, TimeInfo, CalendarEventAttendee, Reminder, EventLocation

    attendees_list = []
    if attendees:
        for uid in attendees:
            attendees_list.append(CalendarEventAttendee.builder().type("user").user_id(uid).build())

    tz = "Asia/Shanghai"
    start_event_time = TimeInfo.builder().timestamp(str(start_time)).timezone(tz).build()
    end_event_time = TimeInfo.builder().timestamp(str(end_time)).timezone(tz).build()
    
    body_builder = CalendarEvent.builder() \
        .summary(summary) \
        .description(description) \
        .start_time(start_event_time) \
        .end_time(end_event_time) \
        .attendees(attendees_list) \
        .reminders([Reminder.builder().minutes(reminder_minutes).build()])
    
    if location:
        body_builder = body_builder.location(EventLocation.builder().name(location).build())
    
    body = body_builder.build()

    request = CreateCalendarEventRequest.builder() \
        .calendar_id("primary") \
        .request_body(body) \
        .build()

    response = client.calendar.v4.calendar_event.create(request)

    if response.success():
        event = response.data.event
        start_dt = datetime.fromtimestamp(int(event.start_time.timestamp), tz=timezone(timedelta(hours=8)))
        end_dt = datetime.fromtimestamp(int(event.end_time.timestamp), tz=timezone(timedelta(hours=8)))
        return (f"会议创建成功！\n标题: {event.summary}\nevent_id: {event.event_id}\n"
                f"时间: {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}\n"
                f"地点: {location or '线上会议'}")
    else:
        return f"创建会议失败: code={response.code}, msg={response.msg}"


@tool
def create_meeting_minutes(event_id: str, title: str, content: list[dict]) -> str:
    """为已创建的会议添加会议纪要。

    注意：当前飞书SDK的创建会议纪要API已更改，此功能可能不可用。
    建议用户直接在飞书中手动记录会议纪要。

    Args:
        event_id: 会议的event_id
        title: 纪要标题
        content: 纪要内容，格式为[{"tag": "paragraph/h1/bullet", "text": "内容"}, ...]
    """
    # 当前飞书SDK的会议纪要API已经改变，这里我们先返回一个提示
    content_str = "\n".join([item.get("text", "") for item in content if isinstance(item, dict)])
    return (f"注意：飞书SDK更新后，会议纪要功能API已变更。\n"
            f"当前无法通过此工具自动创建会议纪要。\n"
            f"建议您直接在飞书中为会议 {event_id} 手动添加纪要。\n"
            f"标题：{title}\n内容预览：\n{content_str[:200]}{'...' if len(content_str) > 200 else ''}")


@tool
def get_meeting_list(calendar_id: str = "primary", page_size: int = 50) -> str:
    """获取会议列表。

    Args:
        calendar_id: 日历ID，默认primary
        page_size: 返回数量，默认50
    """
    client = get_feishu_client()

    from lark_oapi.api.calendar.v4 import ListCalendarEventRequest

    request = ListCalendarEventRequest.builder() \
        .calendar_id(calendar_id) \
        .page_size(page_size) \
        .build()

    response = client.calendar.v4.calendar_event.list(request)

    if response.success():
        events = response.data.items or []
        if not events:
            return "暂无会议"

        lines = ["会议列表:"]
        for e in events:
            start = datetime.fromtimestamp(int(e.start_time.timestamp), tz=timezone(timedelta(hours=8)))
            lines.append(f"- {e.summary} | {start.strftime('%Y-%m-%d %H:%M')} | {e.event_id}")
        return "\n".join(lines)
    else:
        return f"获取会议列表失败: code={response.code}, msg={response.msg}"


feishu_task_tools = [
    schedule_message,
    create_meeting,
    create_meeting_minutes,
    get_meeting_list,
]