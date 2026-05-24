#!/usr/bin/env python3
"""测试修复后的飞书API调用是否可以正常导入和使用。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试导入和基本API结构")
print("=" * 60)

# 测试 1: 导入相关的模块
try:
    import lark_oapi as lark
    from lark_oapi.api.calendar.v4 import (
        CreateCalendarEventRequest,
        CalendarEvent,
        TimeInfo,
        EventLocation,
        Reminder,
        CreateCalendarEventAttendeeRequest,
        CreateCalendarEventAttendeeRequestBody,
        CalendarEventAttendee,
        ListCalendarEventRequest,
    )
    print("✓ 所有导入成功！")
except Exception as e:
    print(f"✗ 导入失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 2: 测试基本的构建器是否可以正常使用
try:
    # 测试 TimeInfo builder
    time_info = TimeInfo.builder() \
        .timestamp("1234567890") \
        .timezone("Asia/Shanghai") \
        .build()
    print("✓ TimeInfo builder 工作正常")

    # 测试 EventLocation builder
    location = EventLocation.builder() \
        .name("线上会议") \
        .build()
    print("✓ EventLocation builder 工作正常")

    # 测试 Reminder builder
    reminder = Reminder.builder() \
        .minutes(15) \
        .build()
    print("✓ Reminder builder 工作正常")

    # 测试 CalendarEventAttendee builder
    attendee = CalendarEventAttendee.builder() \
        .type("user") \
        .user_id("123456") \
        .build()
    print("✓ CalendarEventAttendee builder 工作正常")

    # 测试 CalendarEvent builder
    event_builder = CalendarEvent.builder() \
        .summary("测试会议") \
        .description("这是一个测试会议") \
        .start_time(time_info) \
        .end_time(time_info) \
        .reminders([reminder]) \
        .location(location)
    event = event_builder.build()
    print("✓ CalendarEvent builder 工作正常")

    # 测试 CreateCalendarEventRequest builder
    request = CreateCalendarEventRequest.builder() \
        .calendar_id("primary") \
        .request_body(event) \
        .build()
    print("✓ CreateCalendarEventRequest builder 工作正常")

except Exception as e:
    print(f"✗ 构建器测试失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: 测试我们修改后的工具文件
print("\n" + "=" * 60)
print("测试修改后的工具文件")
print("=" * 60)

try:
    from src.agent.Tools.tool import create_meeting, task_tool_list
    from src.agent.Tools.feishu_task_tool import create_meeting as feishu_create_meeting, feishu_task_tools
    print("✓ 工具文件导入成功")
except Exception as e:
    print(f"✗ 工具文件导入失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("所有测试通过！🎉")
print("=" * 60)
print("\n修复要点：")
print("1. 修复了飞书API调用中的类名错误")
print("2. 使用正确的 CalendarEvent 作为请求体而不是 CreateCalendarEventRequestBody")
print("3. 使用 TimeInfo 而不是 EventTime")
print("4. 使用 EventLocation 而不是简单字符串")
print("5. 使用 CalendarEventAttendee 而不是 Attendee")
print("6. 暂时禁用了会议纪要功能，因为 SDK API 已改变")
