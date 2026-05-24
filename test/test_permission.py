#!/usr/bin/env python
"""Permission system — all-in-one test and data init script.

Usage:
    python test/test_permission.py              # Init data + run all tests
    python test/test_permission.py --init       # Init data only
    python test/test_permission.py --test         # Run tests only (skip init)
    python test/test_permission.py --clean       # Clean + re-init + test
"""
import sqlite3
import shutil
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

CHROMA_DIR = str(ROOT / "chroma_db")
DB_PATH = ROOT / "data.db"


# ─────────────────────────────────────────────────────────────────────────────
# 1. SQL init
# ─────────────────────────────────────────────────────────────────────────────

def init_sql(clean=False):

    if clean:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("DROP TABLE IF EXISTS user_permission")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_permission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL CHECK(tier IN ('T0', 'T1', 'T2', 'T3')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_permission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL CHECK(tier IN ('T0', 'T1', 'T2', 'T3')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    cur = conn.execute("SELECT COUNT(*) FROM user_permission")
    if cur.fetchone()[0] > 0:
        print(f"[SQL] Already populated ({DB_PATH}), skipping")
        conn.close()
        return

    users = [
        ("王刚", "T0"), ("李明", "T1"), ("张伟", "T2"), ("刘洋", "T3"),
        ("赵强", "T0"), ("陈红", "T1"), ("周杰", "T2"), ("吴晓", "T3"),
    ]
    conn.executemany("INSERT INTO user_permission (user_name,tier) VALUES (?,?)", users)
    conn.commit()
    conn.close()

    print(f"[SQL] DB: {DB_PATH}")
    for u in users:
        print(f"       {u[0]} -> {u[1]}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. ChromaDB init
# ─────────────────────────────────────────────────────────────────────────────

def init_chroma(clean=False):
    if clean and os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from src.agent.llm import embedding_model

    tier_docs = {
        "tier0": [
            "【T0机密】公司战略规划：2026年目标实现营收100亿，进入世界500强。",
            "【T0机密】董事会决议：任命王刚为新任CEO，全面负责公司运营。",
            "【T0机密】并购计划：拟收购某新能源公司，交易金额50亿。",
        ],
        "tier1": [
            "【T1内部】部门季度汇报：研发部Q1完成3个核心模块开发。",
            "【T1内部】技术方案：新一代分布式架构设计文档已完成评审。",
            "【T1内部】人员调动：李明调入战略规划部，张伟接管研发组。",
        ],
        "tier2": [
            "【T2受限】项目进度：APP 3.0版本开发完成60%，预计6月上线。",
            "【T2受限】测试报告：上周自动化测试覆盖率提升至85%。",
            "【T2受限】上线清单：V3.0.1版本功能清单及回滚方案。",
        ],
        "tier3": [
            "【T3公开】用户指南：APP新版本功能介绍及使用方法。",
            "【T3公开】常见问题：FAQ - 如何注册、如何找回密码。",
            "【T3公开】版本更新：V3.0.1更新日志。",
        ],
    }

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    for col_name, docs in tier_docs.items():
        texts = text_splitter.create_documents(docs)
        Chroma.from_documents(
            texts,
            embedding_model,
            persist_directory=CHROMA_DIR,
            collection_name=col_name,
        )
        print(f"[ChromaDB] {col_name}: {len(docs)} docs")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_extraction():
    from src.agent.rag_permission import resolve_tier_from_prompt

    cases = [
        ("我是王刚，检索 APP新版本功能介绍", "王刚", "T0"),
        ("我是李明，检索 部门季度汇报", "李明", "T1"),
        ("我是张伟，检索 项目进度", "张伟", "T2"),
        ("我是刘洋，检索 APP新版本功能介绍", "刘洋", "T3"),
        ("帮我查一下明天的天气", "未知用户", "T3"),
    ]
    print("\n[Extract]")
    ok_all = True
    for prompt, exp_name, exp_tier in cases:
        name, tier = resolve_tier_from_prompt(prompt)
        ok = (name == exp_name or exp_name == "未知用户") and tier == exp_tier
        ok_all = ok and ok_all
        print(f"  {'✓' if ok else '✗'} '{prompt[:15]}...' → name={name} tier={tier}")
    return ok_all


def test_collections():
    from src.agent.agent_rag import TIER_COLLECTIONS

    expected = {
        "T0": ["tier0", "tier1", "tier2", "tier3"],
        "T1": ["tier1", "tier2", "tier3"],
        "T2": ["tier2", "tier3"],
        "T3": ["tier3"],
    }
    print("\n[Collections]")
    ok_all = True
    for tier, cols in TIER_COLLECTIONS.items():
        ok = cols == expected[tier]
        ok_all = ok and ok_all
        print(f"  {'✓' if ok else '✗'} {tier} → {cols}")
    return ok_all


def test_retrieval():
    from src.agent.agent_rag import RAGAgent

    rag = RAGAgent(CHROMA_DIR)
    cases = [
        ("我是王刚，检索 公司战略规划", "T0", ["tier0", "tier1", "tier2", "tier3"], "【T0机密】"),
        ("我是李明，检索 部门季度汇报", "T1", ["tier1", "tier2", "tier3"], "【T1内部】"),
        ("我是张伟，检索 项目进度", "T2", ["tier2", "tier3"], "【T2受限】"),
        ("我是刘洋，检索 APP新版本功能介绍", "T3", ["tier3"], "【T3公开】"),
    ]
    print("\n[Retrieval]")
    ok_all = True
    for prompt, tier, collections, doc_prefix in cases:
        context = rag.retrieve(prompt, collections)
        has_t0 = "【T0机密】" in context
        has_exp = doc_prefix in context
        # T1/T2/T3 must not see T0 docs; T0 must see its own
        if tier == "T0":
            ok = has_exp
        else:
            ok = has_exp and not has_t0
        ok_all = ok and ok_all
        print(f"  {'✓' if ok else '✗'} {tier}: {doc_prefix} found={has_exp} T0_leak={has_t0}")
    return ok_all


def test_invoke():
    from src.agent.agent_rag import RAGAgent

    rag = RAGAgent(CHROMA_DIR)
    cases = [
        ("我是王刚，检索 公司战略规划", "T0"),
        ("我是李明，检索 部门季度汇报", "T1"),
        ("我是张伟，检索 项目进度", "T2"),
        ("我是刘洋，检索 APP新版本功能介绍", "T3"),
    ]
    print("\n[Invoke]")
    ok_all = True
    for prompt, tier in cases:
        try:
            result = rag.invoke(prompt, session_id=f"test-{tier}")
            leak = "【T0机密】" in result if tier != "T0" else False
            ok = len(result) > 0 and not leak
            ok_all = ok and ok_all
            print(f"  {'✓' if ok else '✗'} {tier}: chars={len(result)} leak={leak}")
        except Exception as e:
            ok_all = False
            print(f"  ✗ {tier}: EXCEPTION {e}")
    return ok_all


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Permission system test")
    parser.add_argument("--init", action="store_true", help="Init data only")
    parser.add_argument("--test", action="store_true", help="Run tests only (skip init)")
    parser.add_argument("--clean", action="store_true", help="Clean and re-init")
    args = parser.parse_args()

    print("=" * 60)
    print("Permission System — T0/T1/T2/T3 Tiered RAG")
    print("=" * 60)

    if not args.test:
        init_sql(clean=args.clean)
        init_chroma(clean=args.clean)

    if not args.init:
        results = {
            "extract": test_extraction(),
            "collections": test_collections(),
            "retrieval": test_retrieval(),
            "invoke": test_invoke(),
        }

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for name, ok in results.items():
            print(f"  {'✓' if ok else '✗'} {name}")
        print()

        if all(results.values()):
            print("ALL TESTS PASSED")
        else:
            print("SOME TESTS FAILED")
            sys.exit(1)


if __name__ == "__main__":
    main()
