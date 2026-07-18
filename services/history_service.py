"""历史记录服务 - 保存、查询、删除占卜记录"""

import json
import sqlite3

from config import DATABASE_PATH


def _get_db():
    return sqlite3.connect(DATABASE_PATH)


def save_record(question: str, original_id: int, changed_id: int,
                moving_lines: list, yao_values: list, create_time: str = None) -> int:
    """保存占卜记录

    Args:
        question: 占问事项
        original_id: 本卦ID
        changed_id: 变卦ID（无则None）
        moving_lines: 动爻详情列表（dict列表）
        yao_values: 六次投掷详情列表（dict列表）
        create_time: 时间字符串（None则用当前时间）

    Returns:
        记录ID
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO divination_records
            (create_time, question, original_hexagram, changed_hexagram,
             moving_lines, yao_values)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        create_time,
        question,
        original_id,
        changed_id,
        json.dumps(moving_lines, ensure_ascii=False),
        json.dumps(yao_values, ensure_ascii=False),
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def get_records(limit: int = 50) -> list:
    """查询历史记录列表

    Returns:
        记录列表，每条包含id/time/question/本卦名/变卦名/动爻数
    """
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.create_time, r.question,
               h1.name as original_name,
               h2.name as changed_name,
               r.moving_lines
        FROM divination_records r
        LEFT JOIN hexagrams h1 ON r.original_hexagram = h1.id
        LEFT JOIN hexagrams h2 ON r.changed_hexagram = h2.id
        ORDER BY r.create_time DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        record = dict(r)
        moving = json.loads(record["moving_lines"]) if record["moving_lines"] else []
        record["moving_count"] = len(moving)
        results.append(record)
    return results


def get_record_detail(record_id: int) -> dict:
    """查询单条记录详情"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, h1.name as original_name, h1.binary_code as original_binary,
               h2.name as changed_name, h2.binary_code as changed_binary
        FROM divination_records r
        LEFT JOIN hexagrams h1 ON r.original_hexagram = h1.id
        LEFT JOIN hexagrams h2 ON r.changed_hexagram = h2.id
        WHERE r.id = ?
    """, (record_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    record = dict(row)
    record["moving_lines"] = json.loads(record["moving_lines"]) if record["moving_lines"] else []
    record["yao_values"] = json.loads(record["yao_values"]) if record["yao_values"] else []
    return record


def delete_record(record_id: int) -> bool:
    """删除一条记录"""
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM divination_records WHERE id=?", (record_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def save_ai_interpretation(record_id: int, content: str, model: str) -> bool:
    """保存AI解读结果到占卜记录

    Args:
        record_id: 占卜记录ID
        content: AI解读内容
        model: 使用的模型名

    Returns:
        是否保存成功
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE divination_records
        SET ai_interpretation = ?, ai_model = ?
        WHERE id = ?
    """, (content, model, record_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_ai_interpretation(record_id: int) -> dict:
    """获取某条记录的AI解读

    Returns:
        {"content": str, "model": str} 或 None
    """
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ai_interpretation, ai_model FROM divination_records WHERE id = ?
    """, (record_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row["ai_interpretation"]:
        return None
    return {"content": row["ai_interpretation"], "model": row["ai_model"]}
