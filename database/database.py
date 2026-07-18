"""数据库连接与管理"""

import os
import sqlite3

from config import DATABASE_PATH, DATABASE_DIR


def init_db() -> None:
    """初始化数据库 - 如果数据库文件不存在则从JSON导入创建"""
    if os.path.exists(DATABASE_PATH):
        # 已有数据库，执行迁移（添加新字段）
        _migrate()
        return

    # 确保数据库目录存在
    os.makedirs(DATABASE_DIR, exist_ok=True)

    # 内联初始化逻辑（不依赖外部脚本）
    from scripts.init_database import create_database, import_hexagrams, import_yao_lines, import_interpretations, validate_data
    create_database()
    import_hexagrams()
    import_yao_lines()
    import_interpretations()
    validate_data()


def _migrate() -> None:
    """数据库迁移 - 为旧版数据库添加新字段（ALTER TABLE ADD COLUMN）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 获取 divination_records 表的现有列
    cursor.execute("PRAGMA table_info(divination_records)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # v2.0.0: 添加 AI 解读字段
    if "ai_interpretation" not in existing_columns:
        cursor.execute("ALTER TABLE divination_records ADD COLUMN ai_interpretation TEXT")
    if "ai_model" not in existing_columns:
        cursor.execute("ALTER TABLE divination_records ADD COLUMN ai_model TEXT")

    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    if not os.path.exists(DATABASE_PATH):
        init_db()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def close_db() -> None:
    """关闭数据库连接（SQLite每次操作后自动关闭连接）"""
    pass
