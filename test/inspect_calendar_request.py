#!/usr/bin/env python3
"""查看如何正确使用 CreateCalendarEventRequest"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lark_oapi.api.calendar.v4 import CreateCalendarEventRequest
import inspect

# 查看 CreateCalendarEventRequest 的源代码
print("=== CreateCalendarEventRequest ===")
print(inspect.getsource(CreateCalendarEventRequest))

# 查看 builder 类
print("\n=== CreateCalendarEventRequestBuilder ===")
builder = CreateCalendarEventRequest.builder()
print(dir(builder))
print(inspect.getsource(type(builder)))

# 查看 CalendarEvent 相关类
from lark_oapi.api.calendar.v4 import CalendarEvent
print("\n=== CalendarEvent ===")
print(inspect.getsource(CalendarEvent))

# 查看 CalendarEventBuilder
print("\n=== CalendarEventBuilder ===")
event_builder = CalendarEvent.builder()
print(dir(event_builder))
