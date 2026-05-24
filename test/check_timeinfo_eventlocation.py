#!/usr/bin/env python3
"""查看 TimeInfo 和 EventLocation 类"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lark_oapi.api.calendar.v4 import TimeInfo, EventLocation, Reminder, CalendarEventAttendee
import inspect

print("=== TimeInfo ===")
print(inspect.getsource(TimeInfo))

print("\n=== EventLocation ===")
print(inspect.getsource(EventLocation))

print("\n=== Reminder ===")
print(inspect.getsource(Reminder))

print("\n=== CalendarEventAttendee ===")
print(inspect.getsource(CalendarEventAttendee))

# 查找 MeetingMinute 相关的类
from lark_oapi.api.calendar import v4
print("\n=== 查找 MeetingMinute 相关的类 ===")
for symbol in dir(v4):
    if 'Minute' in symbol or 'minute' in symbol:
        print(symbol)
