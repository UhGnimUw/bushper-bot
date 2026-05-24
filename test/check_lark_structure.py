#!/usr/bin/env python3
"""检查飞书SDK的正确API结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lark_oapi as lark

print("=== 检查 lark_oapi.api.calendar.v4 模块 ===")
from lark_oapi.api import calendar
print(dir(calendar))

print("\n=== 检查 lark_oapi.api.calendar.v4 模块 ===")
from lark_oapi.api.calendar import v4
print(dir(v4))

print("\n=== 检查 calendar_event 相关 ===")
print(dir(v4.calendar_event))

print("\n=== 检查 v4.__init__.py 的内容 ===")
import inspect
source = inspect.getsource(v4)
print(source)

print("\n=== 查找所有可能的 Event 相关请求类 ===")
import pkgutil
for _, modname, _ in pkgutil.iter_modules(v4.__path__):
    print(f"\n模块: {modname}")
    try:
        mod = __import__(f'lark_oapi.api.calendar.v4.{modname}', fromlist=[''])
        print(dir(mod))
    except Exception as e:
        print(f"错误: {e}")
