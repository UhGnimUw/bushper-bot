#!/usr/bin/env python3
"""检查如何正确使用飞书SDK"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lark_oapi as lark
from lark_oapi.api.calendar.v4 import CreateCalendarEventRequest

# 创建客户端
client = lark.Client.builder() \
    .app_id("test_id") \
    .app_secret("test_secret") \
    .domain(lark.FEISHU_DOMAIN) \
    .build()

print("=== CreateCalendarEventRequest 的帮助 ===")
help(CreateCalendarEventRequest.builder)

print("\n=== CreateCalendarEventRequestBuilder 的方法 ===")
builder = CreateCalendarEventRequest.builder()
print(dir(builder))

# 让我们尝试查看是否有其他方式
print("\n=== 尝试查找请求体相关类 ===")
from lark_oapi.api.calendar import v4
for symbol in dir(v4):
    if 'RequestBody' in symbol:
        print(symbol)

print("\n=== 查看 v4.calendar_event ===")
print(dir(v4.calendar_event))
