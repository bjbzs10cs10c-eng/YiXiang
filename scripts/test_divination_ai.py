"""测试第四步：占卜结果页AI解读集成

验证内容：
1. AI解读线程类（AIInterpretWorker）
2. 占卜页有AI解读按钮
3. 结果页显示后AI按钮可见
4. 未配置AI时点击按钮提示
5. AI解读结果HTML构建
6. AI解读结果保存到数据库
7. 已有AI解读时自动展示
8. 数据库迁移（旧库添加新字段）
9. reset方法清理AI状态
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox
from unittest.mock import patch, MagicMock

from database.database import init_db
from services.history_service import save_record, save_ai_interpretation, get_ai_interpretation
from services.settings_service import save_ai_config
from ui.divination_page import DivinationPage, AIInterpretWorker


app = None


def get_app():
    global app
    if app is None:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    return app


def _make_mock_result():
    """构造一个模拟占卜结果"""
    return {
        "question": "测试问题",
        "time": "2026-07-14 12:00:00",
        "original_hexagram": {
            "id": 1, "name": "乾", "binary_code": "111111",
            "upper_trigram": "天", "lower_trigram": "天",
            "gua_ci": "元亨利贞", "xiang_ci": "天行健",
        },
        "changed_hexagram": None,
        "moving_lines": [],
        "moving_count": 0,
        "reading_source": "静卦",
        "reading_text": "以卦辞断之",
        "original_yao_lines": [],
        "original_interpretations": [],
        "tosses": [],
    }


def test_ai_worker_class():
    """测试AI解读线程类存在"""
    print("[1] 测试 AIInterpretWorker 类...")
    assert AIInterpretWorker is not None, "AIInterpretWorker 类应存在"
    assert hasattr(AIInterpretWorker, "finished_signal"), "应有 finished_signal"
    assert hasattr(AIInterpretWorker, "error_signal"), "应有 error_signal"
    print("    ✓ AIInterpretWorker 类正常")


def test_ai_button_exists():
    """测试占卜页有AI解读按钮"""
    print("[2] 测试 AI 解读按钮存在...")
    get_app()
    page = DivinationPage()
    assert hasattr(page, "ai_btn"), "占卜页应有 ai_btn 按钮"
    assert page.ai_btn.text() == "AI 解读", f"按钮文字应为'AI 解读'，实际={page.ai_btn.text()}"
    assert not page.ai_btn.isVisible(), "初始状态AI按钮应不可见"
    print("    ✓ AI 解读按钮存在且初始隐藏")


def test_ai_button_visible_after_result():
    """测试结果展示后AI按钮可见"""
    print("[3] 测试结果展示后AI按钮可见...")
    get_app()
    page = DivinationPage()
    page.show()  # 需显示页面，子控件的isVisible才准确
    result = _make_mock_result()
    page._current_result = result

    # 调用 show_result
    page.show_result(result)

    # isVisibleTo 检查相对于父控件的可见性
    assert page.ai_btn.isVisibleTo(page), "结果展示后AI按钮应可见"
    assert page.ai_btn.isEnabled(), "AI按钮应可用"
    assert page.ai_btn.text() == "AI 解读", f"按钮文字应为'AI 解读'，实际={page.ai_btn.text()}"
    print("    ✓ 结果展示后AI按钮可见且可用")


def test_unconfigured_warning():
    """测试未配置AI时点击按钮提示"""
    print("[4] 测试未配置AI时提示...")
    get_app()
    # 确保未配置
    save_ai_config("", "", "", "")

    page = DivinationPage()
    result = _make_mock_result()
    page._current_result = result
    page.show_result(result)

    # Mock QMessageBox
    warned = []
    original_warning = QMessageBox.warning
    QMessageBox.warning = lambda *args: warned.append(args[2]) or QMessageBox.StandardButton.Ok

    try:
        page.on_ai_interpret()
        assert len(warned) > 0, "未配置时应弹出警告"
        assert "未配置" in warned[0], f"提示应包含'未配置'，实际={warned[0]}"
        print(f"    提示内容: {warned[0]}")
    finally:
        QMessageBox.warning = original_warning

    print("    ✓ 未配置时提示正常")


def test_build_ai_html():
    """测试AI解读HTML构建"""
    print("[5] 测试 AI 解读 HTML 构建...")
    get_app()
    page = DivinationPage()

    content = "这是AI解读内容\n第二行\n<script>alert(1)</script>"
    model = "deepseek-v4-flash"
    html = page._build_ai_html(content, model)

    assert "AI 解读" in html, "HTML应包含'AI 解读'标题"
    assert model in html, f"HTML应包含模型名 {model}"
    assert "这是AI解读内容" in html, "HTML应包含内容"
    assert "&lt;script&gt;" in html, "HTML应转义特殊字符"
    assert "<script>" not in html, "HTML不应包含原始script标签"
    assert "<br/>" in html, "换行应转为 <br/>"
    print(f"    HTML片段: {html[:100]}...")
    print("    ✓ AI 解读 HTML 构建正常")


def test_save_ai_interpretation():
    """测试AI解读结果保存到数据库"""
    print("[6] 测试 AI 解读保存到数据库...")
    # 先保存一条占卜记录
    record_id = save_record(
        question="测试保存AI",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-14 10:00:00",
    )

    # 保存AI解读
    content = "这是保存的AI解读内容"
    model = "gpt-5.4-mini"
    success = save_ai_interpretation(record_id, content, model)
    assert success, "保存应成功"

    # 读回验证
    saved = get_ai_interpretation(record_id)
    assert saved is not None, "应能读回AI解读"
    assert saved["content"] == content, f"内容不匹配: {saved['content']}"
    assert saved["model"] == model, f"模型不匹配: {saved['model']}"

    print(f"    record_id: {record_id}")
    print(f"    content: {saved['content']}")
    print(f"    model: {saved['model']}")
    print("    ✓ AI 解读保存和读取正常")


def test_auto_show_saved_ai():
    """测试已有AI解读时自动展示"""
    print("[7] 测试已有AI解读时自动展示...")
    get_app()

    # 保存一条带AI解读的记录
    record_id = save_record(
        question="测试自动展示",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-14 11:00:00",
    )
    save_ai_interpretation(record_id, "预存的AI解读内容", "deepseek-v4-flash")

    page = DivinationPage()
    page._current_result = _make_mock_result()
    page._current_record_id = record_id
    page.show_result(page._current_result)

    # 按钮文字应为"重新AI解读"
    assert page.ai_btn.text() == "重新AI解读", \
        f"已有AI解读时按钮应为'重新AI解读'，实际={page.ai_btn.text()}"

    # 结果HTML应包含AI解读内容
    html = page.result_content.toHtml()
    assert "预存的AI解读内容" in html, "结果页应包含预存的AI解读内容"
    assert "deepseek-v4-flash" in html, "结果页应包含模型名"

    print(f"    按钮文字: {page.ai_btn.text()}")
    print("    ✓ 已有AI解读自动展示正常")


def test_db_migration():
    """测试数据库迁移添加新字段"""
    print("[8] 测试数据库迁移...")
    import sqlite3
    from config import DATABASE_PATH

    init_db()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(divination_records)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    assert "ai_interpretation" in columns, "divination_records 应有 ai_interpretation 字段"
    assert "ai_model" in columns, "divination_records 应有 ai_model 字段"

    print(f"    字段列表: {sorted(columns)}")
    print("    ✓ 数据库迁移正常")


def test_reset_clears_ai_state():
    """测试reset方法清理AI状态"""
    print("[9] 测试 reset 清理 AI 状态...")
    get_app()
    page = DivinationPage()

    # 设置AI状态
    page._current_result = _make_mock_result()
    page._current_record_id = 999
    page.ai_btn.setVisible(True)

    # 执行reset
    page.reset()

    assert page._current_result is None, "reset后 _current_result 应为 None"
    assert page._current_record_id is None, "reset后 _current_record_id 应为 None"
    assert not page.ai_btn.isVisible(), "reset后 AI 按钮应不可见"

    print("    ✓ reset 清理 AI 状态正常")


def test_ai_worker_mock_call():
    """测试AI解读线程的mock调用"""
    print("[10] 测试 AI 解读线程 mock 调用...")
    get_app()

    # 配置一个假AI
    save_ai_config("DeepSeek", "https://api.deepseek.com", "deepseek-v4-flash", "sk-test")

    result = _make_mock_result()
    page = DivinationPage()
    page._current_result = result
    page._current_record_id = None
    page.show_result(result)

    # Mock interpret_divination 返回固定内容
    with patch("ui.divination_page.interpret_divination", return_value="Mock AI解读内容"):
        page.on_ai_interpret()
        # 等待线程完成（用 processEvents）
        import time
        for _ in range(50):
            app.processEvents()
            time.sleep(0.05)
            if page.ai_btn.isEnabled():
                break

    # 验证结果页包含AI解读
    html = page.result_content.toHtml()
    assert "Mock AI解读内容" in html, f"结果页应包含Mock AI内容，html片段: {html[-200:]}"

    print(f"    按钮文字: {page.ai_btn.text()}")
    print("    ✓ AI 解读线程 mock 调用正常")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第四步测试：占卜结果页AI解读集成")
    print("=" * 60)

    init_db()
    print("数据库初始化完成")

    # 备份当前AI配置，防止测试污染
    from scripts.test_utils import backup_ai_config, restore_ai_config
    backup = backup_ai_config()
    print("已备份当前AI配置\n")

    tests = [
        test_ai_worker_class,
        test_ai_button_exists,
        test_ai_button_visible_after_result,
        test_unconfigured_warning,
        test_build_ai_html,
        test_save_ai_interpretation,
        test_auto_show_saved_ai,
        test_db_migration,
        test_reset_clears_ai_state,
        test_ai_worker_mock_call,
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
