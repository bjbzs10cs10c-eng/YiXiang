"""测试第七步：数据库扩展

验证内容：
1. 新库初始化包含 ai_interpretation 和 ai_model 字段
2. 旧库迁移正确添加新字段（模拟旧库场景）
3. save_ai_interpretation 保存AI解读
4. get_ai_interpretation 读取AI解读
5. 已有记录的AI字段默认为NULL
6. 重复保存覆盖旧AI解读
7. 历史记录列表查询不因新字段崩溃
8. 记录详情查询包含AI字段
9. 删除记录时AI字段一并删除
10. settings表正常工作（AI配置存储）
"""

import sys
import os
import sqlite3
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db
from services.history_service import (save_record, get_records, get_record_detail,
                                       delete_record, save_ai_interpretation,
                                       get_ai_interpretation)
from services.settings_service import get_ai_config, save_ai_config, get_setting, set_setting
from config import DATABASE_PATH


def _get_columns(table_name: str) -> set:
    """获取指定表的所有列名"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()
    return columns


def test_schema_has_ai_fields():
    """测试新库schema包含AI字段"""
    print("[1] 测试 schema 包含 AI 字段...")
    init_db()
    columns = _get_columns("divination_records")
    assert "ai_interpretation" in columns, f"应有 ai_interpretation 字段，实际: {columns}"
    assert "ai_model" in columns, f"应有 ai_model 字段，实际: {columns}"
    print(f"    字段列表: {sorted(columns)}")
    print("    ✓ schema 包含 AI 字段")


def test_old_db_migration():
    """测试旧库迁移（模拟旧版数据库升级）"""
    print("[2] 测试旧库迁移...")
    # 备份当前数据库
    backup_path = DATABASE_PATH + ".backup"
    has_backup = os.path.exists(DATABASE_PATH)
    if has_backup:
        shutil.copy2(DATABASE_PATH, backup_path)

    try:
        # 创建一个旧版数据库（无AI字段）
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS divination_records")
        cursor.execute("""
            CREATE TABLE divination_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                question TEXT,
                original_hexagram INTEGER,
                changed_hexagram INTEGER,
                moving_lines TEXT,
                yao_values TEXT,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()

        # 确认旧库无AI字段
        old_cols = _get_columns("divination_records")
        assert "ai_interpretation" not in old_cols, "旧库应无 ai_interpretation"
        assert "ai_model" not in old_cols, "旧库应无 ai_model"

        # 执行迁移
        init_db()

        # 验证新字段已添加
        new_cols = _get_columns("divination_records")
        assert "ai_interpretation" in new_cols, "迁移后应有 ai_interpretation"
        assert "ai_model" in new_cols, "迁移后应有 ai_model"
        print(f"    迁移前字段: {sorted(old_cols)}")
        print(f"    迁移后字段: {sorted(new_cols)}")
        print("    ✓ 旧库迁移正常")
    finally:
        # 恢复原数据库
        if has_backup:
            shutil.move(backup_path, DATABASE_PATH)
        else:
            os.remove(DATABASE_PATH)
        init_db()  # 重新初始化


def test_save_ai_interpretation():
    """测试保存AI解读"""
    print("[3] 测试保存 AI 解读...")
    record_id = save_record(
        question="测试保存AI解读",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 10:00:00",
    )

    content = "这是测试的AI解读内容"
    model = "deepseek-v4-flash"
    success = save_ai_interpretation(record_id, content, model)
    assert success, "保存应成功"
    print(f"    record_id: {record_id}")
    print(f"    content: {content}")
    print(f"    model: {model}")
    print("    ✓ 保存 AI 解读正常")


def test_get_ai_interpretation():
    """测试读取AI解读"""
    print("[4] 测试读取 AI 解读...")
    record_id = save_record(
        question="测试读取AI解读",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 11:00:00",
    )
    save_ai_interpretation(record_id, "读取测试内容", "gpt-5.4-mini")

    result = get_ai_interpretation(record_id)
    assert result is not None, "应能读取AI解读"
    assert result["content"] == "读取测试内容"
    assert result["model"] == "gpt-5.4-mini"
    print(f"    content: {result['content']}")
    print(f"    model: {result['model']}")
    print("    ✓ 读取 AI 解读正常")


def test_null_default_value():
    """测试已有记录的AI字段默认为NULL"""
    print("[5] 测试已有记录 AI 字段默认 NULL...")
    # 保存一条记录但不保存AI解读
    record_id = save_record(
        question="测试默认NULL",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 12:00:00",
    )

    result = get_ai_interpretation(record_id)
    assert result is None, "未保存AI解读时应返回None"
    print(f"    record_id: {record_id}")
    print(f"    result: {result}")
    print("    ✓ 默认 NULL 正常")


def test_overwrite_ai_interpretation():
    """测试重复保存覆盖旧AI解读"""
    print("[6] 测试覆盖保存...")
    record_id = save_record(
        question="测试覆盖保存",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 13:00:00",
    )
    save_ai_interpretation(record_id, "第一次解读", "model-v1")
    save_ai_interpretation(record_id, "第二次解读", "model-v2")

    result = get_ai_interpretation(record_id)
    assert result["content"] == "第二次解读", "应被第二次覆盖"
    assert result["model"] == "model-v2", "模型应被覆盖"
    print(f"    最终 content: {result['content']}")
    print(f"    最终 model: {result['model']}")
    print("    ✓ 覆盖保存正常")


def test_get_records_works():
    """测试历史记录列表查询不因新字段崩溃"""
    print("[7] 测试历史记录列表查询...")
    save_record(
        question="列表查询测试",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 14:00:00",
    )

    records = get_records(50)
    assert len(records) > 0, "应有记录"
    # 每条记录应包含必要字段
    r = records[0]
    assert "id" in r
    assert "create_time" in r
    assert "question" in r
    assert "original_name" in r
    assert "moving_count" in r
    print(f"    记录数: {len(records)}")
    print(f"    第一条: id={r['id']}, question={r['question'][:15]}")
    print("    ✓ 历史记录列表查询正常")


def test_get_record_detail_works():
    """测试记录详情查询包含AI字段"""
    print("[8] 测试记录详情查询...")
    record_id = save_record(
        question="详情查询测试",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 15:00:00",
    )
    save_ai_interpretation(record_id, "详情中的AI解读", "test-model")

    detail = get_record_detail(record_id)
    assert detail is not None
    assert "ai_interpretation" in detail, "详情应包含 ai_interpretation 字段"
    assert "ai_model" in detail, "详情应包含 ai_model 字段"
    assert detail["ai_interpretation"] == "详情中的AI解读"
    assert detail["ai_model"] == "test-model"
    print(f"    ai_interpretation: {detail['ai_interpretation']}")
    print(f"    ai_model: {detail['ai_model']}")
    print("    ✓ 记录详情查询正常")


def test_delete_record_cascade_ai():
    """测试删除记录时AI字段一并删除"""
    print("[9] 测试删除记录级联清理...")
    record_id = save_record(
        question="删除测试",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-18 16:00:00",
    )
    save_ai_interpretation(record_id, "将被删除的AI解读", "to-delete")

    # 删除记录
    success = delete_record(record_id)
    assert success, "删除应成功"

    # AI解读应也消失
    result = get_ai_interpretation(record_id)
    assert result is None, "删除后AI解读应为None"
    print(f"    record_id: {record_id}")
    print(f"    删除后查询: {result}")
    print("    ✓ 删除记录级联清理正常")


def test_settings_table_for_ai_config():
    """测试settings表正常工作（AI配置存储）"""
    print("[10] 测试 settings 表存储 AI 配置...")

    # 清理
    save_ai_config("", "", "", "")

    # 写入
    save_ai_config("DeepSeek", "https://api.deepseek.com", "deepseek-v4-flash", "sk-test-123")

    # 读取验证
    config = get_ai_config()
    assert config["provider"] == "DeepSeek"
    assert config["endpoint"] == "https://api.deepseek.com"
    assert config["model"] == "deepseek-v4-flash"
    assert config["api_key"] == "sk-test-123", f"API Key解密失败: {config['api_key']}"
    assert config["configured"] is True

    # 直接查询settings表
    provider_value = get_setting("ai_provider")  # 实际key由config.py定义
    # 验证settings表确实有数据
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM settings")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 4, f"settings表应有至少4条AI配置，实际: {count}"

    print(f"    provider: {config['provider']}")
    print(f"    endpoint: {config['endpoint']}")
    print(f"    model: {config['model']}")
    print(f"    api_key: {config['api_key']}")
    print(f"    settings表记录数: {count}")
    print("    ✓ settings 表存储正常")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第七步测试：数据库扩展")
    print("=" * 60)

    init_db()
    print("数据库初始化完成")

    # 备份当前AI配置，防止测试污染
    from scripts.test_utils import backup_ai_config, restore_ai_config
    backup = backup_ai_config()
    print("已备份当前AI配置\n")

    tests = [
        test_schema_has_ai_fields,
        test_old_db_migration,
        test_save_ai_interpretation,
        test_get_ai_interpretation,
        test_null_default_value,
        test_overwrite_ai_interpretation,
        test_get_records_works,
        test_get_record_detail_works,
        test_delete_record_cascade_ai,
        test_settings_table_for_ai_config,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"    ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

    # 恢复AI配置
    restore_ai_config(backup)
    print("已恢复AI配置")

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
