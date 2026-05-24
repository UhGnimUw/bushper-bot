# 权限分级 RAG 系统

基于用户身份（从提示词提取）实现 T0-T3 四级权限控制的数据隔离。

## 权限层级

| 层级 | 可查询 Collection | 说明 |
|------|------------------|------|
| T0   | tier0, tier1, tier2, tier3 | 最高权限，可访问全部 |
| T1   | tier1, tier2, tier3        | 可访问 T1 及以下 |
| T2   | tier2, tier3               | 可访问 T2 及以下 |
| T3   | tier3                      | 仅可访问 T3（公开） |

**提权规则**：T1 可调用 T2、T3；T0 可调用所有。

## 用户身份识别

通过提示词中的 `我是XXX` 提取用户身份：

```
我是王刚，检索 APP新版本功能介绍    → 王刚 → T0
我是刘洋，检索 项目进度            → 刘洋 → T3
```

无身份识别时默认 T3（最低权限）。

## 数据库

SQLite：`data.db`（统一数据库文件）

```sql
CREATE TABLE user_permission (
    id INTEGER PRIMARY KEY,
    user_name TEXT NOT NULL UNIQUE,
    tier TEXT CHECK(tier IN ('T0','T1','T2','T3'))
);
```

## 向量数据库

ChromaDB：`./chroma_db/`，4个 Collection：

- `t0` — T0机密文档
- `t1` — T1内部文档
- `t2` — T2受限文档
- `t3` — T3公开文档

## 快速开始

### 1. 安装依赖

```bash
conda activate finrpa
pip install langchain-chroma langchain-core langchain-text-splitters pydantic
```

### 2. 初始化数据

```bash
cd /mnt/e/test/proj/myagent

# 初始化 SQL + ChromaDB（默认跳过已有数据）
python test/test_permission.py --init

# 清理旧数据后重新初始化
python test/test_permission.py --clean
```

### 3. 运行测试

```bash
python test/test_permission.py
```

### 4. 仅运行测试（跳过初始化）

```bash
python test/test_permission.py --test
```

输出示例：
```
[SQL] DB: sql/user_permission.db
       王刚 -> T0
       李明 -> T1
       ...
[ChromaDB] tier0: 3 docs
[ChromaDB] tier1: 3 docs
[ChromaDB] tier2: 3 docs
[ChromaDB] tier3: 3 docs

[Extract]
  ✓ '我是王刚，检索...' → name=王刚 tier=T0
[Collections]
  ✓ T0 → ['tier0', 'tier1', 'tier2', 'tier3']
[Retrieval]
  ✓ T3: 【T3公开】 found=True T0_leak=False
[Invoke]
  ✓ T0: chars=... leak=False
  ✓ T3: chars=... leak=False

ALL TESTS PASSED
```

### 4. 程序中调用

```python
from src.agent.agent import get_agent

# 提示词包含"我是XXX"自动识别权限
result = get_agent("我是刘洋，检索 APP新版本功能介绍", session_id="s1").invoke(
    "我是刘洋，检索 APP新版本功能介绍", session_id="s1"
)
```

## 文件说明

```
sql/user_permission.sql          # 权限表 DDL + 测试数据
src/agent/agent_rag.py          # 分层 RAG Agent（含 load_tier_test_data）
src/agent/agent.py              # Agent 路由（RAGWithMemory 调用链路）
test/test_permission.py         # 完整测试脚本（init + test）
```
