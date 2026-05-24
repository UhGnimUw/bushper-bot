#!/usr/bin/env python3
import inspect
import lark_oapi as lark

print("=== lark_oapi version ===")
print(inspect.getsource(lark))

print("\n=== lark.Client.builder ===")
print(inspect.signature(lark.Client.builder))

print("\n=== lark.Client 类 ===")
client_builder = lark.Client.builder()
print(dir(client_builder))

print("\n=== 尝试创建 client 并检查属性 ===")
client = lark.Client.builder() \
    .app_id("test-id") \
    .app_secret("test-secret") \
    .log_level(lark.LogLevel.INFO) \
    .build()

print(f"client type: {type(client)}")
print(f"client._config: {client._config}, type: {type(client._config)}")

print("\n=== client._config 的属性 ===")
print(dir(client._config))

print("\n=== client._config 的属性值 ===")
for attr in dir(client._config):
    if not attr.startswith('_'):
        try:
            val = getattr(client._config, attr)
            print(f"  {attr} = {repr(val)}")
        except Exception as e:
            print(f"  {attr} = ERROR: {e}")

print("\n=== 另外尝试添加 domain ===")
client_with_domain = lark.Client.builder() \
    .app_id("test-id") \
    .app_secret("test-secret") \
    .domain("https://open.feishu.cn") \
    .log_level(lark.LogLevel.INFO) \
    .build()
print(f"client_with_domain._config.domain = {repr(client_with_domain._config.domain)}")

