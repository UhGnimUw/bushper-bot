from langchain_core.tools import tool

@tool
def search_city_graph(query: str) -> str:
    """搜索中国城市和省份的知识图谱信息。

    当用户询问城市信息、省份信息、城市间关系（如哪些城市与某城市接壤）时使用此工具。

    Args:
        query: 查询关键词，可以是：
              - 城市名：如"杭州市"、"北京市"
              - 省份名：如"浙江省"、"广东省"
              - 关系查询：如"与杭州市接壤的城市"、"浙江省有哪些城市"
    """
    import json
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent.parent.parent / "city_graph.db"
    if not db_path.exists():
        return f"城市知识图谱数据库不存在：{db_path}。请先运行初始化脚本。"

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 首先尝试精确匹配城市
        cur.execute(
            "SELECT * FROM cities WHERE name LIKE ? OR anothername LIKE ? LIMIT 10",
            (f"%{query}%", f"%{query}%")
        )
        cities = [dict(row) for row in cur.fetchall()]

        if cities:
            results = []
            for city in cities:
                # 获取该城市所属省份
                cur.execute(
                    "SELECT name FROM provinces WHERE id = ?",
                    (city["province_id"],)
                )
                province = cur.fetchone()
                province_name = province["name"] if province else "未知"

                # 获取与该城市接壤的城市
                cur.execute("""
                    SELECT c.name, c.population, c.rgdp, c.car, c.anothername
                    FROM city_relations cr
                    JOIN cities c ON cr.source_id = c.id OR cr.target_id = c.id
                    WHERE (cr.source_id = ? OR cr.target_id = ?) AND c.id != ?
                """, (city["id"], city["id"], city["id"]))
                neighbors = cur.fetchall()

                neighbor_info = ""
                if neighbors:
                    neighbor_list = [n["name"] for n in neighbors]
                    neighbor_info = f"\n接壤城市：{', '.join(neighbor_list)}"
                else:
                    neighbor_info = "\n接壤城市：无"

                results.append(
                    f"【{city['name']}】{city['anothername'] or ''}\n"
                    f"所属省份：{province_name}\n"
                    f"人口：{city['population'] or '未知'}\n"
                    f"GDP：{city['rgdp'] or '未知'}\n"
                    f"车牌号：{city['car'] or '未知'}\n"
                    f"英文名：{city['englishname'] or '未知'}{neighbor_info}"
                )

            conn.close()
            return "=".join(results) if len(results) > 1 else results[0] if results else ""

        # 尝试匹配省份
        cur.execute(
            "SELECT * FROM provinces WHERE name LIKE ? LIMIT 10",
            (f"%{query}%",)
        )
        provinces = [dict(row) for row in cur.fetchall()]

        if provinces:
            results = []
            for province in provinces:
                # 获取该省份下的城市
                cur.execute(
                    "SELECT name, population, rgdp FROM cities WHERE province_id = ? LIMIT 20",
                    (province["id"],)
                )
                cities_in_province = cur.fetchall()

                city_list = [c["name"] for c in cities_in_province]
                results.append(
                    f"【{province['name']}】\n"
                    f"简称：{province.get('abbr', '未知')}\n"
                    f"下辖城市（{len(city_list)}个）：{', '.join(city_list) if city_list else '暂无数据'}"
                )

            conn.close()
            return "\n---\n".join(results) if len(results) > 1 else results[0] if results else ""

        conn.close()
        return f"未找到与「{query}」相关的城市或省份信息"

    except Exception as e:
        return f"查询出错：{e}"


def init_city_graph_db(db_path: str = "./city_graph.db"):
    """初始化城市知识图谱数据库。

    运行此函数将创建并填充城市、省份和城市关系数据。
    """
    import json
    import sqlite3
    from pathlib import Path

    db_file = Path(db_path)
    if db_file.exists():
        print(f"数据库已存在：{db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 创建表
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS provinces (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            abbr TEXT
        );

        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            province_id INTEGER,
            population TEXT,
            rgdp TEXT,
            car TEXT,
            englishname TEXT,
            anothername TEXT,
            FOREIGN KEY (province_id) REFERENCES provinces(id)
        );

        CREATE TABLE IF NOT EXISTS city_relations (
            id INTEGER PRIMARY KEY,
            source_id INTEGER,
            target_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES cities(id),
            FOREIGN KEY (target_id) REFERENCES cities(id)
        );

        CREATE INDEX IF NOT EXISTS idx_city_name ON cities(name);
        CREATE INDEX IF NOT EXISTS idx_province_name ON provinces(name);
    """)

    # 读取数据文件
    graph_dir = Path(__file__).parent.parent.parent.parent / "graph_view" / "html" / "data"
    relation_file = Path(__file__).parent.parent.parent.parent / "graph_view" / "graph" / "relation.json"

    # 加载省份数据
    province_file = graph_dir / "province_name.txt"
    if province_file.exists():
        provinces = []
        for line in province_file.read_text().strip().split("\n"):
            name = line.strip()
            if name:
                provinces.append((name, name[:2]))
        cur.executemany("INSERT INTO provinces (name, abbr) VALUES (?, ?)", provinces)
        print(f"已加载 {len(provinces)} 个省份")

    # 加载城市数据 - 从city_chinese_name.txt和records.json
    city_name_file = graph_dir / "city_chinese_name.txt"
    records_file = relation_file

    # 城市名列表
    city_names = set()
    if city_name_file.exists():
        for line in city_name_file.read_text().strip().split("\n"):
            name = line.strip()
            if name:
                city_names.add(name)

    # 从关系文件中提取城市信息
    city_info = {}
    if records_file.exists():
        try:
            relations = json.loads(records_file.read_text())
            for rel in relations:
                for end_key in ["start", "end"]:
                    node = rel["p"][end_key]
                    if node["labels"] and node["labels"][0] == "城市":
                        props = node["properties"]
                        city_info[props["name"]] = {
                            "name": props.get("name", ""),
                            "englishname": props.get("englishname", ""),
                            "population": props.get("population", ""),
                            "rgdp": props.get("rgdp", ""),
                            "car": props.get("car", ""),
                            "anothername": props.get("anothername", ""),
                        }
        except json.JSONDecodeError:
            print("Warning: relation.json parsing failed, using simplified data")

    # 城市名补充
    for name in city_names:
        if name not in city_info:
            city_info[name] = {
                "name": name,
                "englishname": "",
                "population": "",
                "rgdp": "",
                "car": "",
                "anothername": "",
            }

    # 插入城市数据（简化版：只关联到第一个省份）
    city_id_map = {}
    city_records = []
    for idx, (name, info) in enumerate(city_info.items()):
        # 默认归属（需要更精确的归属关系可以后续扩展）
        province_id = 1  # 默认省份
        city_records.append((
            info["name"],
            province_id,
            info["population"],
            info["rgdp"],
            info["car"],
            info["englishname"],
            info["anothername"],
        ))
        city_id_map[name] = idx

    cur.executemany(
        "INSERT INTO cities (name, province_id, population, rgdp, car, englishname, anothername) VALUES (?, ?, ?, ?, ?, ?, ?)",
        city_records
    )
    print(f"已加载 {len(city_records)} 个城市")

    # 插入城市关系
    relations_list = []
    if records_file.exists():
        try:
            relations = json.loads(records_file.read_text())
            for rel in relations:
                start_node = rel["p"]["start"]
                end_node = rel["p"]["end"]
                if start_node["labels"] and end_node["labels"]:
                    start_name = start_node["properties"].get("name", "")
                    end_name = end_node["properties"].get("name", "")
                    if start_name in city_id_map and end_name in city_id_map:
                        relations_list.append((city_id_map[start_name], city_id_map[end_name]))
        except json.JSONDecodeError:
            print("Warning: relation.json parsing failed, skipping relations")

    cur.executemany(
        "INSERT INTO city_relations (source_id, target_id) VALUES (?, ?)",
        relations_list
    )
    print(f"已加载 {len(relations_list)} 个城市关系")

    conn.commit()
    conn.close()
    print(f"城市知识图谱数据库初始化完成：{db_path}")