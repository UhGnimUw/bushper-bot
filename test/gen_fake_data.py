#!/usr/bin/env python
"""构造假数据：8 个部门 + 100 个人，存入本地 SQLite 数据库。

用法：
    python test/gen_fake_data.py
"""
import random
import io
import json
from pathlib import Path
import time
import argparse

import sqlite3


# ------------------------------------------------------------------
# 配置
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
DATA_DB = BASE_DIR / "data.db"


# ------------------------------------------------------------------
# 假数据
# ------------------------------------------------------------------
DEPARTMENTS = [
    ("研发部", "负责产品研发、技术架构与实现"),
    ("产品部", "负责产品规划、需求分析与市场调研"),
    ("设计部", "负责 UI/UX 设计、品牌视觉与交互体验"),
    ("市场部", "负责市场推广、品牌宣传与活动策划"),
    ("销售部", "负责客户拓展、合同签订与业绩完成"),
    ("人力资源部", "负责招聘、培训、绩效管理与员工关系"),
    ("财务部", "负责财务核算、预算管理与资金管理"),
    ("行政部", "负责后勤保障、资产管理与日常行政事务"),
]

NAMES = [
    "张伟", "王芳", "李明", "刘洋", "陈静", "杨帆", "赵磊", "黄丽", "周强", "吴敏",
    "徐涛", "孙悦", "马超", "朱婷", "胡健", "郭雪", "林峰", "何欢", "高远", "罗辉",
    "梁志", "宋雨", "郑浩", "谢军", "韩冰", "唐寅", "冯凯", "董琳", "萧然", "程鹏",
    "曹文", "袁媛", "邓涛", "彭亮", "卢杰", "崔鑫", "蒋晨", "蔡红", "丁俊", "余勇",
    "苏华", "戴霞", "钱伟", "卫卓", "沈青", "卫东", "李秀", "张军", "王丽", "陈龙",
    "李娜", "周婷", "吴磊", "徐明", "孙健", "马超", "朱琳", "胡平", "郭峰", "林梅",
    "何静", "高鹏", "罗丹", "梁超", "宋燕", "郑鑫", "谢勇", "韩磊", "唐娜", "冯超",
    "董芳", "萧亮", "程浩", "曹磊", "袁超", "邓芳", "彭俊", "卢超", "崔芳", "蒋勇",
    "蔡平", "丁霞", "余伟", "苏磊", "戴超", "钱勇", "卫平", "沈芳", "卫超", "李勇",
    "张亮", "王健", "李磊", "刘刚", "陈芳", "杨超", "赵平", "黄磊", "周亮", "吴超",
]

GENDERS = ["男", "女"]

DESCRIPTIONS = [
    "负责前端页面开发与性能优化",
    "后端 API 开发与微服务架构",
    "数据库设计与 SQL 优化",
    "iOS/Android 移动端开发",
    "产品需求分析与原型设计",
    "数据分析与可视化报表",
    "机器学习模型训练与部署",
    "DevOps 流水线与容器编排",
    "网络安全防护与漏洞修复",
    "UI 界面设计与交互优化",
    "品牌视觉设计与宣传物料",
    "市场活动策划与执行",
    "客户关系维护与合同谈判",
    "财务报表编制与成本核算",
    "人员招聘与培训组织",
    "资产采购与库存管理",
    "日常行政事务与后勤支持",
    "考勤管理与薪酬核算",
    "合同审核与风险控制",
    "供应商管理与采购谈判",
]


def gen_people(dept_id: int, n: int) -> list:
    """生成 n 条人员记录，department_id = dept_id。允许重名。"""
    rows = []
    for _ in range(n):
        name = random.choice(NAMES)
        gender = random.choice(GENDERS)
        age = random.randint(22, 58)
        phone = f"138{random.randint(10000000, 99999999)}"
        desc = random.choice(DESCRIPTIONS)
        rows.append((dept_id, name, gender, age, phone, desc))
    return rows


def create_tables(cur):
    """建表（如果不存在）。"""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_id INTEGER REFERENCES department(id),
            name VARCHAR(50) NOT NULL,
            gender VARCHAR(4),
            age INTEGER,
            phone VARCHAR(20),
            description TEXT
        )
    """)


def get_or_create_departments(cur):
    """获取或创建部门，返回 dept_ids"""
    cur.execute("SELECT id, name FROM department ORDER BY id")
    existing = {name: id for id, name in cur.fetchall()}

    if existing:
        print(f"已存在 {len(existing)} 个部门")
        return sorted(existing.values())

    print("插入部门...")
    for name, desc in DEPARTMENTS:
        cur.execute("INSERT INTO department (name, description) VALUES (?, ?)", (name, desc))
    cur.execute("SELECT id FROM department ORDER BY id")
    return [row[0] for row in cur.fetchall()]


def main():
    parser = argparse.ArgumentParser(description="生成假数据")
    args = parser.parse_args()

    print(f"使用数据库：{DATA_DB}")
    conn = sqlite3.connect(str(DATA_DB))
    cur = conn.cursor()

    print("建表...")
    create_tables(cur)
    conn.commit()

    dept_ids = get_or_create_departments(cur)
    conn.commit()

    all_people = []

    print("插入人员（100 人）...")
    for dept_id in dept_ids:
        n_people = random.randint(10, 15)
        all_people.extend(gen_people(dept_id, n_people))

    if len(all_people) > 100:
        all_people = all_people[:100]
    elif len(all_people) < 100:
        while len(all_people) < 100:
            dept_id = random.choice(dept_ids)
            extra = gen_people(dept_id, 1)
            all_people.extend(extra)

    total_people = len(all_people)
    print(f"开始插入 {total_people} 人...")

    start_time = time.time()
    for i in range(0, total_people, 10):
        batch = all_people[i:i + 10]
        end_idx = min(i + 10, total_people)
        print(f"\r进度: {end_idx}/{total_people} ({end_idx/total_people*100:.1f}%)", end='', flush=True)

        cur.executemany(
            "INSERT INTO people (dept_id, name, gender, age, phone, description) VALUES (?, ?, ?, ?, ?, ?)",
            batch
        )
        conn.commit()

    print(f"\n人员插入耗时：{time.time() - start_time:.2f}秒")

    cur.execute("SELECT COUNT(*) FROM people")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM department")
    dept_count = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"完成：{dept_count} 个部门，{total} 条人员记录。")


if __name__ == "__main__":
    main()
