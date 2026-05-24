#!/usr/bin/env python3
"""查找飞书SDK中所有正确的类名"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lark_oapi.api.calendar import v4

print("=== lark_oapi.api.calendar.v4 中的所有符号 ===")
all_symbols = dir(v4)
for symbol in sorted(all_symbols):
    if not symbol.startswith('_'):
        print(symbol)

print("\n=== 查找 Event 相关的请求/响应类 ===")
for symbol in sorted(all_symbols):
    if not symbol.startswith('_') and ('Event' in symbol or 'event' in symbol):
        print(symbol)

print("\n=== 查找 Calendar 相关的请求/响应类 ===")
for symbol in sorted(all_symbols):
    if not symbol.startswith('_') and ('Calendar' in symbol or 'calendar' in symbol):
        print(symbol)

print("\n=== 查找 Attendee 相关的请求/响应类 ===")
for symbol in sorted(all_symbols):
    if not symbol.startswith('_') and ('Attendee' in symbol or 'attendee' in symbol):
        print(symbol)

print("\n=== 查找 Minute 相关的请求/响应类 ===")
for symbol in sorted(all_symbols):
    if not symbol.startswith('_') and ('Minute' in symbol or 'minute' in symbol):
        print(symbol)
