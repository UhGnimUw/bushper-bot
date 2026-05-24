#!/usr/bin/env python3
"""查看 MeetingMinute 类"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lark_oapi.api.calendar.v4 import MeetingMinute
import inspect

print("=== MeetingMinute ===")
print(inspect.getsource(MeetingMinute))

# 查看 CreateCalendarEventMeetingMinuteRequest
from lark_oapi.api.calendar.v4 import CreateCalendarEventMeetingMinuteRequest
print("\n=== CreateCalendarEventMeetingMinuteRequest ===")
print(inspect.getsource(CreateCalendarEventMeetingMinuteRequest))
