"""数据库初始化脚本 - 建表、导入JSON数据、校验"""

import json
import os
import sqlite3
import sys

# 将项目根目录加入路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config import DATABASE_PATH, DATA_DIR, HEXAGRAMS_JSON, YAO_LINES_JSON, INTERPRETATIONS_JSON

SCHEMA_PATH = os.path.join(PROJECT_ROOT, "database", "schema.sql")


def load_json(filepath: str) -> list:
    """加载JSON文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def create_database() -> None:
    """创建数据库并执行建表SQL"""
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"[OK] 数据库创建完成: {DATABASE_PATH}")


def import_hexagrams() -> int:
    """导入六十四卦数据"""
    data = load_json(HEXAGRAMS_JSON)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    count = 0
    for item in data:
        cursor.execute("""
            INSERT INTO hexagrams (id, sequence, name, symbol, binary_code,
                                   upper_trigram, lower_trigram,
                                   gua_ci, tuan_ci, xiang_ci)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["id"], item["sequence"], item["name"], item["symbol"],
            item["binary_code"], item["upper_trigram"], item["lower_trigram"],
            item["gua_ci"], item["tuan_ci"], item["xiang_ci"]
        ))
        count += 1
    conn.commit()
    conn.close()
    print(f"[OK] 导入六十四卦: {count} 条")
    return count


def import_yao_lines() -> int:
    """导入三百八十四爻数据"""
    data = load_json(YAO_LINES_JSON)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    count = 0
    for item in data:
        cursor.execute("""
            INSERT INTO yao_lines (hexagram_id, position, yao_name, yao_type,
                                   original_text, translation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item["hexagram_id"], item["position"], item["yao_name"],
            item["yao_type"], item["original_text"], item["translation"]
        ))
        count += 1
    conn.commit()
    conn.close()
    print(f"[OK] 导入爻辞: {count} 条")
    return count


def import_interpretations() -> int:
    """导入解释数据"""
    filepath = INTERPRETATIONS_JSON
    if not os.path.exists(filepath):
        print("[SKIP] interpretations.json 不存在，跳过")
        return 0

    data = load_json(filepath)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    count = 0
    for item in data:
        cursor.execute("""
            INSERT INTO interpretations (target_type, target_id, source, title, content)
            VALUES (?, ?, ?, ?, ?)
        """, (
            item["target_type"], item["target_id"], item["source"],
            item["title"], item["content"]
        ))
        count += 1
    conn.commit()
    conn.close()
    print(f"[OK] 导入解释: {count} 条")
    return count


def validate_data() -> bool:
    """数据校验"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    errors = []

    # 校验64卦
    cursor.execute("SELECT COUNT(*) FROM hexagrams")
    hex_count = cursor.fetchone()[0]
    if hex_count != 64:
        errors.append(f"六十四卦数量错误: 期望64, 实际{hex_count}")

    # 校验binary_code唯一
    cursor.execute("SELECT COUNT(DISTINCT binary_code) FROM hexagrams")
    unique_count = cursor.fetchone()[0]
    if unique_count != 64:
        errors.append(f"binary_code不唯一: 期望64个不同值, 实际{unique_count}")

    # 校验爻辞：384爻 + 乾坤2用爻 = 386条
    cursor.execute("SELECT COUNT(*) FROM yao_lines")
    yao_count = cursor.fetchone()[0]
    if yao_count != 386:
        errors.append(f"爻辞数量错误: 期望386(含用爻), 实际{yao_count}")

    # 校验每卦至少6爻（乾坤7爻含用爻）
    cursor.execute("""
        SELECT hexagram_id, COUNT(*) as cnt
        FROM yao_lines
        GROUP BY hexagram_id
        HAVING cnt < 6
    """)
    bad_rows = cursor.fetchall()
    if bad_rows:
        errors.append(f"以下卦爻数不足6: {bad_rows}")

    # 校验乾坤用爻
    cursor.execute("""
        SELECT hexagram_id, yao_name FROM yao_lines
        WHERE position = 7 ORDER BY hexagram_id
    """)
    yong_rows = cursor.fetchall()
    yong_expected = {(1, "用九"), (2, "用六")}
    yong_actual = set(yong_rows)
    if yong_actual != yong_expected:
        errors.append(f"用爻数据错误: 期望{yong_expected}, 实际{yong_actual}")

    conn.close()

    if errors:
        print("[FAIL] 数据校验失败:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("[OK] 数据校验通过: 64卦 + 386爻(含用爻) + binary_code唯一")
    return True


def init():
    """完整初始化流程"""
    print("=" * 50)
    print("易象 - 数据库初始化")
    print("=" * 50)

    # 检查JSON文件
    for name, path in [("hexagrams", HEXAGRAMS_JSON), ("yao_lines", YAO_LINES_JSON)]:
        if not os.path.exists(path):
            print(f"[ERROR] 数据文件不存在: {path}")
            sys.exit(1)

    # 删除旧数据库
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print("[OK] 删除旧数据库")

    # 建表
    create_database()

    # 导入数据
    import_hexagrams()
    import_yao_lines()
    import_interpretations()

    # 校验
    if not validate_data():
        sys.exit(1)

    print("=" * 50)
    print("初始化完成!")
    print("=" * 50)


if __name__ == "__main__":
    init()
