"""解释查询服务 - 查询卦辞、爻辞、多版本解释"""

import sqlite3
from typing import Optional

from config import DATABASE_PATH


def _get_db():
    return sqlite3.connect(DATABASE_PATH)


def get_hexagram_by_id(hexagram_id: int) -> Optional[dict]:
    """根据ID查询卦象"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hexagrams WHERE id=?", (hexagram_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_hexagram_by_name(name: str) -> Optional[dict]:
    """根据卦名查询卦象"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hexagrams WHERE name LIKE ?", (f"%{name}%",))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_hexagrams() -> list:
    """查询全部六十四卦（按序号）"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, sequence, name, symbol, binary_code, upper_trigram, lower_trigram FROM hexagrams ORDER BY sequence")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_yao_lines(hexagram_id: int) -> list:
    """查询某卦所有爻辞"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM yao_lines WHERE hexagram_id=? AND position<=6 ORDER BY position", (hexagram_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_interpretations(target_type: str, target_id: int) -> list:
    """查询解释"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interpretations WHERE target_type=? AND target_id=?", (target_type, target_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
