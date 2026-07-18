"""测试第六步：卦库页AI解读集成

验证内容：
1. LibraryAIWorker 线程类存在
2. 卦库页有AI解读按钮
3. 选中卦象后AI按钮可见
4. 未配置AI时点击提示
5. AI解读HTML构建（含XSS转义）
6. 切换卦象时正确管理状态
7. AI解读线程mock调用
8. AI解读失败错误展示
9. 加载中提示
10. interpret_hexagram函数被调用（而非interpret_divination）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox
from unittest.mock import patch

from database.database import init_db
from services.settings_service import save_ai_config
from services.interpretation_service import get_all_hexagrams, get_hexagram_by_id, get_yao_lines
from ui.library_page import LibraryPage, LibraryAIWorker


app = None


def get_app():
    global app
    if app is None:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    return app


def test_worker_class():
    """测试 LibraryAIWorker 线程类"""
    print("[1] 测试 LibraryAIWorker 类...")
    assert LibraryAIWorker is not None
    assert hasattr(LibraryAIWorker, "finished_signal")
    assert hasattr(LibraryAIWorker, "error_signal")
    print("    ✓ LibraryAIWorker 类正常")


def test_ai_button_exists():
    """测试卦库页有AI按钮"""
    print("[2] 测试 AI 解读按钮存在...")
    get_app()
    page = LibraryPage()
    assert hasattr(page, "ai_btn"), "卦库页应有 ai_btn"
    assert page.ai_btn.text() == "AI 解读", f"按钮文字应为'AI 解读'，实际={page.ai_btn.text()}"
    print("    ✓ AI 解读按钮存在")


def test_ai_button_visible_on_select():
    """测试选中卦象后AI按钮可见"""
    print("[3] 测试选中卦象后AI按钮可见...")
    get_app()
    page = LibraryPage()
    page.show()

    assert len(page.hexagrams) > 0, "应有64卦数据"

    # 选中第一卦
    page.list_widget.setCurrentRow(0)
    app.processEvents()

    assert page.ai_btn.isVisibleTo(page), "选中卦象后AI按钮应可见"
    assert page.ai_btn.isEnabled(), "AI按钮应可用"
    assert page.ai_btn.text() == "AI 解读"
    print(f"    当前卦: {page._current_hexagram['name']}")
    print(f"    按钮文字: {page.ai_btn.text()}")
    print("    ✓ 选中卦象后AI按钮可见")


def test_unconfigured_warning():
    """测试未配置AI时点击提示"""
    print("[4] 测试未配置AI时提示...")
    get_app()
    save_ai_config("", "", "", "")

    page = LibraryPage()
    page.show()
    page.list_widget.setCurrentRow(0)
    app.processEvents()

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


def test_build_ai_html():
    """测试AI解读HTML构建"""
    print("[5] 测试 AI 解读 HTML 构建...")
    get_app()
    page = LibraryPage()

    content = "卦库页AI解读\n第二行<b>加粗</b>\n<script>alert(1)</script>"
    model = "deepseek-v4-flash"
    html = page._build_ai_html(content, model)

    assert "AI 解读" in html
    assert model in html
    assert "卦库页AI解读" in html
    assert "&lt;b&gt;" in html, "应转义<b>标签"
    assert "&lt;script&gt;" in html, "应转义<script>标签"
    assert "<script>" not in html, "不应包含原始script标签"
    assert "<br/>" in html, "换行应转为 <br/>"
    print("    ✓ AI 解读 HTML 构建正常（含XSS转义）")


def test_switch_hexagram_resets_state():
    """测试切换卦象时正确重置状态"""
    print("[6] 测试切换卦象时状态重置...")
    get_app()
    page = LibraryPage()
    page.show()

    # 选中第一卦
    page.list_widget.setCurrentRow(0)
    app.processEvents()
    first_id = page._current_hexagram_id
    first_name = page._current_hexagram['name']

    # 模拟AI解读中状态
    page.ai_btn.setText("AI 解读中...")
    page.ai_btn.setEnabled(False)

    # 切换到第二卦
    page.list_widget.setCurrentRow(1)
    app.processEvents()
    second_id = page._current_hexagram_id

    assert second_id != first_id, "应切换到不同的卦"
    assert page.ai_btn.text() == "AI 解读", "切换后按钮文字应重置"
    assert page.ai_btn.isEnabled(), "切换后按钮应可用"
    print(f"    第一卦: id={first_id}, 第二卦: id={second_id}")
    print(f"    当前卦名: {page._current_hexagram['name']}")
    print("    ✓ 切换卦象时状态正确重置")


def test_ai_worker_mock_call():
    """测试AI解读线程mock调用"""
    print("[7] 测试 AI 解读线程 mock 调用...")
    get_app()

    save_ai_config("DeepSeek", "https://api.deepseek.com", "deepseek-v4-flash", "sk-test")

    page = LibraryPage()
    page.show()
    page.list_widget.setCurrentRow(0)
    app.processEvents()

    # Mock interpret_hexagram
    with patch("ui.library_page.interpret_hexagram", return_value="卦库Mock AI内容"):
        page.on_ai_interpret()
        import time
        for _ in range(50):
            app.processEvents()
            time.sleep(0.05)
            if page.ai_btn.isEnabled():
                break

    html = page.detail.toHtml()
    assert "卦库Mock AI内容" in html, f"详情应包含Mock内容，html片段: {html[-200:]}"

    print(f"    按钮文字: {page.ai_btn.text()}")
    print("    ✓ AI 解读线程 mock 调用正常")


def test_ai_error_display():
    """测试AI解读失败错误展示"""
    print("[8] 测试 AI 解读失败错误展示...")
    get_app()

    save_ai_config("DeepSeek", "https://api.deepseek.com", "deepseek-v4-flash", "sk-test")

    page = LibraryPage()
    page.show()
    page.list_widget.setCurrentRow(0)
    app.processEvents()

    from services.ai_service import AIError

    # Mock interpret_hexagram 抛出异常
    def raise_error(hexagram, yao_lines=None):
        raise AIError("测试错误信息", "test_error")

    with patch("ui.library_page.interpret_hexagram", side_effect=raise_error):
        page.on_ai_interpret()
        import time
        for _ in range(50):
            app.processEvents()
            time.sleep(0.05)
            if page.ai_btn.isEnabled():
                break

    html = page.detail.toHtml()
    assert "AI 解读失败" in html, "应展示失败标题"
    assert "测试错误信息" in html, "应展示错误信息"
    assert page.ai_btn.text() == "AI 解读", "失败后按钮应恢复为'AI 解读'"
    print("    ✓ AI 解读失败错误展示正常")


def test_loading_hint():
    """测试加载中提示"""
    print("[9] 测试加载中提示...")
    get_app()

    save_ai_config("DeepSeek", "https://api.deepseek.com", "deepseek-v4-flash", "sk-test")

    page = LibraryPage()
    page.show()
    page.list_widget.setCurrentRow(0)
    app.processEvents()

    # Mock一个延迟返回的interpret_hexagram
    def slow_return(hexagram, yao_lines=None):
        import time
        time.sleep(0.1)
        return "延迟返回内容"

    with patch("ui.library_page.interpret_hexagram", side_effect=slow_return):
        page.on_ai_interpret()
        app.processEvents()
        # 此时按钮应禁用且文字改变
        assert page.ai_btn.text() == "AI 解读中...", f"按钮应显示'AI 解读中...'，实际={page.ai_btn.text()}"
        assert not page.ai_btn.isEnabled(), "AI解读中按钮应禁用"

        html = page.detail.toHtml()
        assert "AI 解读中" in html, "详情区应显示加载中提示"

        # 等待完成
        import time
        for _ in range(50):
            app.processEvents()
            time.sleep(0.05)
            if page.ai_btn.isEnabled():
                break

    print("    ✓ 加载中提示正常")


def test_uses_interpret_hexagram_not_divination():
    """测试使用interpret_hexagram而非interpret_divination"""
    print("[10] 测试使用 interpret_hexagram 函数...")
    # 检查 library_page.py 中导入的是 interpret_hexagram
    import ui.library_page as lib_module
    assert hasattr(lib_module, "interpret_hexagram"), "应导入 interpret_hexagram"
    assert not hasattr(lib_module, "interpret_divination"), "不应导入 interpret_divination"

    # 检查 LibraryAIWorker 中调用的是 interpret_hexagram
    import inspect
    source = inspect.getsource(LibraryAIWorker)
    assert "interpret_hexagram" in source, "LibraryAIWorker应调用 interpret_hexagram"
    assert "interpret_divination" not in source, "LibraryAIWorker不应调用 interpret_divination"

    print("    ✓ 正确使用 interpret_hexagram 函数")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第六步测试：卦库页AI解读集成")
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
        test_build_ai_html,
        test_switch_hexagram_resets_state,
        test_ai_worker_mock_call,
        test_ai_error_display,
        test_loading_hint,
        test_uses_interpret_hexagram_not_divination,
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
