"""数据库连接与管理"""

import os
import sqlite3

from config import DATABASE_PATH, DATABASE_DIR


def init_db() -> None:
    """初始化数据库 - 如果数据库文件不存在则从JSON导入创建"""
    if os.path.exists(DATABASE_PATH):
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
