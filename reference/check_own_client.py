#!/usr/bin/env python3
import sys
sys.path.insert(0, '/mnt/e/test/proj/myagent')
import lark_oapi as lark
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Testing lark.Client ===")
app_id = os.getenv('FEISHU_APP_ID')
app_secret = os.getenv('FEISHU_APP_SECRET')

print(f"App ID: {app_id}")

client = lark.Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .log_level(lark.LogLevel.DEBUG) \
    .build()

print(f"Client config domain: {client._config.domain}")

print("=== Done ===")

