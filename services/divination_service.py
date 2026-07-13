"""占卜服务 - 完整占卜流程编排

流程：输入问题 → 六次投掷 → 本卦 → 动爻 → 变卦 → 解释
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional

from core.coin import toss_three_coins
from core.yao import Yao
from core.hexagram import Hexagram
from config import DATABASE_PATH


def _get_db():
    """获取数据库连接"""
    return sqlite3.connect(DATABASE_PATH)


def _query_hexagram(binary_code: str) -> Optional[dict]:
    """根据binary_code查询卦象信息"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hexagrams WHERE binary_code=?", (binary_code,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def _query_yao_lines(hexagram_id: int) -> list:
    """查询某卦所有爻辞"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM yao_lines WHERE hexagram_id=? ORDER BY position",
        (hexagram_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _query_interpretations(target_type: str, target_id: int) -> list:
    """查询解释"""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM interpretations WHERE target_type=? AND target_id=?",
        (target_type, target_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _determine_reading_yao(moving_lines: list, yaos: list) -> Optional[dict]:
    """根据动爻数量决定看哪一爻的爻辞

    断卦规则（来自answers1.txt）：
    - 0个动爻：看本卦卦辞（返回None，由调用方处理）
    - 1个动爻：看该动爻爻辞
    - 2个动爻：同性看在上者，异性看阴爻
    - 3个动爻：看中间那个动爻（排序后第2个）
    - 4个动爻：看下方那个静爻
    - 5个动爻：看唯一的静爻
    - 6个动爻：看变卦卦辞（返回None，由调用方处理）
    """
    count = len(moving_lines)

    if count == 0 or count == 6:
        # 静卦看本卦卦辞，六爻全动看变卦卦辞
        return None

    if count == 1:
        # 看该动爻
        pos = moving_lines[0]
        return {"position": pos, "hexagram": "original"}

    if count == 2:
        # 两动爻：同性看在上者，异性看阴爻
        yao_a = yaos[moving_lines[0] - 1]
        yao_b = yaos[moving_lines[1] - 1]
        if yao_a.yin_yang == yao_b.yin_yang:
            # 同性：看位置在上者
            pos = max(moving_lines)
        else:
            # 异性：看阴爻
            for p in moving_lines:
                if yaos[p - 1].yin_yang == "阴":
                    pos = p
                    break
        return {"position": pos, "hexagram": "original"}

    if count == 3:
        # 看中间那个动爻（排序后第2个）
        sorted_moving = sorted(moving_lines)
        pos = sorted_moving[1]
        return {"position": pos, "hexagram": "original"}

    if count == 4:
        # 看下方那个静爻
        all_positions = {1, 2, 3, 4, 5, 6}
        static_lines = sorted(all_positions - set(moving_lines))
        pos = static_lines[0]  # 位置靠下的静爻
        return {"position": pos, "hexagram": "original"}

    if count == 5:
        # 看唯一的静爻
        all_positions = {1, 2, 3, 4, 5, 6}
        static_lines = list(all_positions - set(moving_lines))
        pos = static_lines[0]
        return {"position": pos, "hexagram": "original"}

    return None


def start_divination(question: str) -> dict:
    """执行完整占卜流程

    Args:
        question: 占问事项

    Returns:
        完整占卜结果字典
    """
    # 1. 六次投掷，从初爻到上爻
    tosses = []
    yaos = []
    for i in range(6):
        result = toss_three_coins()
        tosses.append(result)
        yao = Yao(value=result["value"], position=i + 1)
        yaos.append(yao)

    # 2. 生成卦象
    hexagram = Hexagram(yaos)
    original_binary = hexagram.binary_code

    # 3. 查询本卦信息
    original_hex = _query_hexagram(original_binary)
    if not original_hex:
        raise ValueError(f"未找到binary_code={original_binary}的卦象")

    # 4. 动爻判断
    moving_lines = hexagram.get_moving_lines()

    # 5. 变卦计算
    changing_binary = hexagram.get_changing_binary()
    changed_hex = None
    if changing_binary:
        changed_hex = _query_hexagram(changing_binary)

    # 6. 构建动爻详情（JSON格式）
    moving_details = []
    for pos in moving_lines:
        yao = yaos[pos - 1]
        moving_details.append({
            "position": pos,
            "value": yao.value,
            "name": yao.name
        })

    # 7. 构建投掷详情（JSON格式）
    yao_values_json = []
    for i, toss in enumerate(tosses):
        yao_values_json.append({
            "position": i + 1,
            "coins": toss["coins"],
            "value": toss["value"],
            "name": toss["name"]
        })

    # 8. 查询本卦爻辞
    original_yao_lines = _query_yao_lines(original_hex["id"])

    # 9. 查询变卦爻辞（如有）
    changed_yao_lines = []
    if changed_hex:
        changed_yao_lines = _query_yao_lines(changed_hex["id"])

    # 10. 查询本卦解释
    original_interpretations = _query_interpretations("hexagram", original_hex["id"])

    # 11. 查询变卦解释（如有）
    changed_interpretations = []
    if changed_hex:
        changed_interpretations = _query_interpretations("hexagram", changed_hex["id"])

    # 12. 断卦：决定看哪条爻辞
    reading_info = _determine_reading_yao(moving_lines, yaos)
    reading_text = None
    reading_source = None

    if reading_info is None:
        if len(moving_lines) == 0:
            # 静卦：看本卦卦辞
            reading_text = original_hex["gua_ci"]
            reading_source = "本卦卦辞"
        else:
            # 六爻全动：看变卦卦辞
            if changed_hex:
                # 乾坤特殊处理：用九/用六
                if changed_hex["id"] == 1:
                    # 变卦为乾，看用九
                    for yl in changed_yao_lines:
                        if yl["position"] == 7:
                            reading_text = yl["original_text"]
                            reading_source = "用九"
                            break
                elif changed_hex["id"] == 2:
                    # 变卦为坤，看用六
                    for yl in changed_yao_lines:
                        if yl["position"] == 7:
                            reading_text = yl["original_text"]
                            reading_source = "用六"
                            break
                else:
                    reading_text = changed_hex["gua_ci"]
                    reading_source = "变卦卦辞"
    else:
        # 看某爻爻辞
        pos = reading_info["position"]
        for yl in original_yao_lines:
            if yl["position"] == pos:
                reading_text = yl["original_text"]
                reading_source = yl["yao_name"]
                break

    return {
        "question": question,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tosses": yao_values_json,
        "yaos": [{"position": y.position, "value": y.value, "yin_yang": y.yin_yang,
                   "changing": y.changing, "name": y.name} for y in yaos],
        "original_hexagram": original_hex,
        "original_yao_lines": original_yao_lines,
        "original_interpretations": original_interpretations,
        "moving_lines": moving_details,
        "moving_count": len(moving_lines),
        "changed_hexagram": changed_hex,
        "changed_yao_lines": changed_yao_lines,
        "changed_interpretations": changed_interpretations,
        "reading_text": reading_text,
        "reading_source": reading_source,
    }


def save_record(result: dict) -> int:
    """保存占卜记录到数据库

    Args:
        result: start_divination返回的结果

    Returns:
        记录ID
    """
    conn = _get_db()
    cursor = conn.cursor()

    original_id = result["original_hexagram"]["id"]
    changed_id = result["changed_hexagram"]["id"] if result["changed_hexagram"] else None

    cursor.execute("""
        INSERT INTO divination_records
            (create_time, question, original_hexagram, changed_hexagram,
             moving_lines, yao_values)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        result["time"],
        result["question"],
        original_id,
        changed_id,
        json.dumps(result["moving_lines"], ensure_ascii=False),
        json.dumps(result["tosses"], ensure_ascii=False),
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id
