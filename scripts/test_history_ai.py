"""测试第五步：历史记录页AI解读集成

验证内容：
1. HistoryAIWorker 线程类存在
2. 历史页有AI解读按钮
3. 选中记录后AI按钮可见
4. 未配置AI时点击提示
5. 已有AI解读自动展示（按钮变"重新AI解读"）
6. 从详情构建result格式
7. AI解读HTML构建（复用）
8. AI解读结果保存到数据库
9. 无记录时AI按钮隐藏
10. AI解读线程mock调用
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox
from unittest.mock import patch

from database.database import init_db
from services.history_service import (get_records, save_record, save_ai_interpretation,
                                       get_ai_interpretation, delete_record, get_record_detail)
from services.settings_service import save_ai_config
from ui.history_page import HistoryPage, HistoryAIWorker


app = None


def get_app():
    global app
    if app is None:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    return app


def _ensure_test_record():
    """确保有一条测试记录，返回record_id"""
    records = get_records(1)
    if records:
        return records[0]['id']
    # 没有记录则创建一条
    return save_record(
        question="历史页AI测试",
        original_id=1,
        changed_id=None,
        moving_lines=[],
        yao_values=[],
        create_time="2026-07-14 15:00:00",
    )


def test_worker_class():
    """测试 HistoryAIWorker 线程类"""
    print("[1] 测试 HistoryAIWorker 类...")
    assert HistoryAIWorker is not None
    assert hasattr(HistoryAIWorker, "finished_signal")
    assert hasattr(HistoryAIWorker, "error_signal")
    # 信号参数：finished_signal(str, str, int)
    print("    ✓ HistoryAIWorker 类正常")


def test_ai_button_exists():
    """测试历史页有AI按钮"""
    print("[2] 测试 AI 解读按钮存在...")
    get_app()
    page = HistoryPage()
    assert hasattr(page, "ai_btn"), "历史页应有 ai_btn"
    print("    ✓ AI 解读按钮存在")


def test_ai_button_visible_on_select():
    """测试选中记录后AI按钮可见"""
    print("[3] 测试选中记录后AI按钮可见...")
    get_app()
    page = HistoryPage()
    page.show()

    if len(page.records) == 0:
        # 无记录时跳过
        print("    (无记录，跳过)")
        return

    # 选中第一条
    page.list_widget.setCurrentRow(0)
    app.processEvents()

    assert page.ai_btn.isVisibleTo(page), "选中记录后AI按钮应可见"
    assert page.ai_btn.isEnabled(), "AI按钮应可用"
    print(f"    按钮文字: {page.ai_btn.text()}")
    print("    ✓ 选中记录后AI按钮可见")


def test_unconfigured_warning():
    """测试未配置AI时提示"""
    print("[4] 测试未配置AI时提示...")
    get_app()
    save_ai_config("", "", "", "")

    page = HistoryPage()
    page.show()
    page._current_detail = {"id": 1, "original_hexagram": 1, "question": "test",
                            "create_time": "2026", "moving_lines": [], "yao_values": []}
    page._current_record_id = 1

    warned = []
    original_warning = QMessageBox.warning
    QMessageBox.warning = lambda *args: warned.append(args[2]) or QMessageBox.StandardButton.Ok

    try:
        page.on_ai_interpret()
        assert len(warned) > 0, "未配置时应弹出警告"
        assert "未配置" in warned[0]
        print(f"    提示: {warned[0]}")
    finally:
        QMessageBox.warning = original_warning

    print("    ✓ 未配置时提示正常")


def test_auto_show_saved_ai():
    """测试已有AI解读自动展示"""
    print("[5] 测试已有AI解读自动展示...")
    get_app()

    record_id = _ensure_test_record()
    # 保存一条AI解读
    save_ai_interpretation(record_id, "历史页预存AI解读内容", "deepseek-v4-flash")

    page = HistoryPage()
    page.show()

    # 找到并选中该记录
    target_row = None
    for i, r in enumerate(page.records):
        if r['id'] == record_id:
            target_row = i
            break

    if target_row is not None:
        page.list_widget.setCurrentRow(target_row)
        app.processEvents()

        assert page.ai_btn.text() == "重新AI解读", \
            f"已有AI解读时按钮应为'重新AI解读'，实际={page.ai_btn.text()}"

        html = page.detail.toHtml()
        assert "历史页预存AI解读内容" in html, "详情应包含预存的AI解读内容"
        assert "deepseek-v4-flash" in html, "详情应包含模型名"
        print(f"    按钮文字: {page.ai_btn.text()}")
        print("    ✓ 已有AI解读自动展示正常")
    else:
        print("    (未找到测试记录，跳过)")

    # 清理
    # delete_record(record_id)  # 保留记录，避免影响其他测试


def test_build_result_from_detail():
    """测试从详情构建result格式"""
    print("[6] 测试从详情构建result格式...")
    get_app()
    record_id = _ensure_test_record()
    detail = get_record_detail(record_id)

    page = HistoryPage()
    result = page._build_result_from_detail(detail)

    assert result is not None, "构建result不应为None"
    assert "question" in result
    assert "time" in result
    assert "original_hexagram" in result
    assert "changed_hexagram" in result
    assert "moving_lines" in result
    assert "moving_count" in result
    assert "reading_source" in result
    assert "reading_text" in result
    assert "original_yao_lines" in result
    assert "original_interpretations" in result

    print(f"    question: {result['question']}")
    print(f"    reading_source: {result['reading_source']}")
    print(f"    moving_count: {result['moving_count']}")
    print("    ✓ 从详情构建result正常")


def test_build_ai_html():
    """测试AI解读HTML构建"""
    print("[7] 测试 AI 解读 HTML 构建...")
    get_app()
    page = HistoryPage()

    content = "历史页AI解读\n第二行<b>加粗</b>"
    model = "gpt-5.4-mini"
    html = page._build_ai_html(content, model)

    assert "AI 解读" in html
    assert model in html
    assert "历史页AI解读" in html
    assert "&lt;b&gt;" in html, "应转义<b>标签"
    print("    ✓ AI 解读 HTML 构建正常")


def test_save_and_read_ai():
    """测试AI解读保存和读取（历史页专用）"""
    print("[8] 测试 AI 解读保存和读取...")
    record_id = _ensure_test_record()

    content = "历史页保存测试AI内容"
    model = "kimi-k2.6"
    success = save_ai_interpretation(record_id, content, model)
    assert success

    saved = get_ai_interpretation(record_id)
    assert saved is not None
    assert saved["content"] == content
    assert saved["model"] == model

    print(f"    record_id: {record_id}")
    print(f"    content: {saved['content']}")
    print("    ✓ 保存和读取正常")


def test_no_record_hides_button():
    """测试无记录时AI按钮隐藏"""
    print("[9] 测试无记录时AI按钮状态...")
    get_app()
    page = HistoryPage()

    # 无论有无记录，refresh都会正确设置按钮状态
    if len(page.records) == 0:
        assert not page.ai_btn.isVisible(), "无记录时AI按钮应不可见"
        print("    ✓ 无记录时AI按钮隐藏")
    else:
        # 有记录时，未选中状态下按钮可能不可见（需选中后才显示）
        print(f"    (当前有{len(page.records)}条记录，未选中状态下按钮不显示)")


def test_ai_worker_mock_call():
    """测试AI解读线程mock调用"""
    print("[10] 测试 AI 解读线程 mock 调用...")
    get_app()

    save_ai_config("DeepSeek", "https://api.deepseek.com", "deepseek-v4-flash", "sk-test")
    record_id = _ensure_test_record()

    page = HistoryPage()
    page.show()

    # 选中测试记录
    target_row = None
    for i, r in enumerate(page.records):
        if r['id'] == record_id:
            target_row = i
            break

    if target_row is None:
        print("    (未找到测试记录，跳过)")
        return

    page.list_widget.setCurrentRow(target_row)
    app.processEvents()

    # Mock interpret_divination
    with patch("ui.history_page.interpret_divination", return_value="历史页Mock AI内容"):
        page.on_ai_interpret()
        import time
        for _ in range(50):
            app.processEvents()
            time.sleep(0.05)
            if page.ai_btn.isEnabled():
                break

    html = page.detail.toHtml()
    assert "历史页Mock AI内容" in html, f"详情应包含Mock内容，html片段: {html[-200:]}"

    # 验证保存到了数据库
    saved = get_ai_interpretation(record_id)
    assert saved is not None, "AI解读应已保存"
    assert "历史页Mock AI内容" in saved["content"]

    print(f"    按钮文字: {page.ai_btn.text()}")
    print(f"    数据库保存: {saved['content'][:30]}...")
    print("    ✓ AI 解读线程 mock 调用正常")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第五步测试：历史记录页AI解读集成")
    print("=" * 60)

    init_db()
    print("数据库初始化完成")

    # 备份当前AI配置，防止测试污染
    from scripts.test_utils import backup_ai_config, restore_ai_config
    backup = backup_ai_config()
    print("已备份当前AI配置\n")

    tests = [
        test_worker_class,
        test_ai_button_exists,
        test_ai_button_visible_on_select,
        test_unconfigured_warning,
        test_auto_show_saved_ai,
        test_build_result_from_detail,
        test_build_ai_html,
        test_save_and_read_ai,
        test_no_record_hides_button,
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
