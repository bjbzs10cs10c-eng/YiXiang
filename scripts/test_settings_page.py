"""测试设置页 - 验证UI组件、表单逻辑、配置保存

GUI测试需要 QApplication，用非交互方式验证核心逻辑：
1. 页面实例化
2. 服务商下拉列表完整
3. 切换服务商自动填充端点
4. 表单校验（空字段提示）
5. 保存配置到数据库
6. 主窗口导航栏新增"设置"入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox, QLineEdit
from PySide6.QtCore import Qt

from database.database import init_db
from config import AI_PROVIDERS, AI_PROVIDER_MODELS, AI_DEFAULT_PROVIDER
from services.settings_service import get_ai_config, save_ai_config
from ui.settings_page import SettingsPage
from ui.main_window import MainWindow


# 全局 QApplication（GUI测试必须）
app = None


def get_app():
    global app
    if app is None:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    return app


def test_page_instantiation():
    """测试设置页能正常实例化"""
    print("[1] 测试设置页实例化...")
    get_app()
    page = SettingsPage()
    assert page is not None, "设置页实例化失败"
    print("    ✓ 设置页实例化成功")


def test_provider_combo():
    """测试服务商下拉列表完整"""
    print("[2] 测试服务商下拉列表...")
    get_app()
    page = SettingsPage()
    combo = page.provider_combo

    assert combo.count() == len(AI_PROVIDERS), \
        f"下拉项数应={len(AI_PROVIDERS)}，实际={combo.count()}"

    for name in AI_PROVIDERS.keys():
        assert combo.findText(name) >= 0, f"下拉列表缺少: {name}"

    print(f"    下拉列表共 {combo.count()} 项:")
    for i in range(combo.count()):
        print(f"      - {combo.itemText(i)}")
    print("    ✓ 服务商列表完整")


def test_default_provider():
    """测试无配置时默认选中DeepSeek"""
    print("[2.5] 测试默认服务商为DeepSeek...")
    get_app()
    # 确保无配置
    save_ai_config("", "", "", "")
    page = SettingsPage()

    assert page.provider_combo.currentText() == AI_DEFAULT_PROVIDER, \
        f"无配置时应默认选中{AI_DEFAULT_PROVIDER}，实际={page.provider_combo.currentText()}"
    assert page.endpoint_input.text() == "https://api.deepseek.com", \
        f"默认端点应为DeepSeek，实际={page.endpoint_input.text()}"
    assert "deepseek-v4-flash" in page.model_input.placeholderText(), \
        f"模型提示应含deepseek-v4-flash，实际={page.model_input.placeholderText()}"

    print(f"    默认服务商: {page.provider_combo.currentText()}")
    print(f"    默认端点: {page.endpoint_input.text()}")
    print(f"    模型提示: {page.model_input.placeholderText()}")
    print("    ✓ 默认服务商正确")


def test_model_placeholder():
    """测试切换服务商时模型提示更新"""
    print("[2.6] 测试模型名提示随服务商切换...")
    get_app()
    page = SettingsPage()

    # DeepSeek
    page.provider_combo.setCurrentText("DeepSeek")
    ph = page.model_input.placeholderText()
    assert "deepseek-v4-flash" in ph, f"DeepSeek提示错误: {ph}"
    print(f"    DeepSeek: {ph}")

    # OpenAI
    page.provider_combo.setCurrentText("OpenAI")
    ph = page.model_input.placeholderText()
    assert "gpt-5" in ph, f"OpenAI提示错误: {ph}"
    print(f"    OpenAI: {ph}")

    # 智谱GLM
    page.provider_combo.setCurrentText("智谱GLM")
    ph = page.model_input.placeholderText()
    assert "glm-4" in ph, f"智谱提示错误: {ph}"
    print(f"    智谱GLM: {ph}")

    # Kimi
    page.provider_combo.setCurrentText("Kimi (月之暗面)")
    ph = page.model_input.placeholderText()
    assert "kimi-k2" in ph, f"Kimi提示错误: {ph}"
    print(f"    Kimi: {ph}")

    print("    ✓ 模型提示随服务商切换正常")


def test_provider_auto_fill():
    """测试切换服务商自动填充端点"""
    print("[3] 测试切换服务商自动填充端点...")
    get_app()
    page = SettingsPage()

    # 先切换到OpenAI（触发信号），再切回DeepSeek
    page.provider_combo.setCurrentText("OpenAI")
    assert page.endpoint_input.text() == "https://api.openai.com/v1", \
        f"OpenAI端点填充错误: {page.endpoint_input.text()}"

    # 切换到 DeepSeek
    page.provider_combo.setCurrentText("DeepSeek")
    assert page.endpoint_input.text() == "https://api.deepseek.com", \
        f"DeepSeek端点填充错误: {page.endpoint_input.text()}"

    # 切换到 Gemini
    page.provider_combo.setCurrentText("Gemini")
    assert "generativelanguage.googleapis.com" in page.endpoint_input.text(), \
        f"Gemini端点填充错误: {page.endpoint_input.text()}"

    # 切换到 Claude（官方无OpenAI兼容端点，端点保持不自动填充）
    page.provider_combo.setCurrentText("Claude")
    # Claude端点为空，不自动填充，端点保持上一个值
    print(f"    Claude端点(不自动填充): {page.endpoint_input.text()}")

    # 切换到自定义（端点保持原值）
    page.provider_combo.setCurrentText("自定义")
    print(f"    DeepSeek → {get_endpoint_check(page, 'DeepSeek')}")
    print(f"    OpenAI → {get_endpoint_check(page, 'OpenAI')}")
    print(f"    Gemini → {get_endpoint_check(page, 'Gemini')}")
    print(f"    Claude → (无自动填充，保持原值)")
    print("    ✓ 切换服务商自动填充正常")


def get_endpoint_check(page, provider):
    page.provider_combo.setCurrentText(provider)
    return page.endpoint_input.text()


def test_form_validation_empty():
    """测试表单校验 - 空字段"""
    print("[4] 测试表单校验（空字段）...")
    get_app()
    page = SettingsPage()

    # 清空所有字段
    page.endpoint_input.clear()
    page.model_input.clear()
    page.apikey_input.clear()

    # Mock QMessageBox 避免弹窗阻塞
    warned = []
    original_warning = QMessageBox.warning
    QMessageBox.warning = lambda *args: warned.append(args[2]) or QMessageBox.StandardButton.Ok

    try:
        # 触发保存 - 应提示
        page.on_save()
        assert len(warned) > 0, "空字段应触发警告"
        print(f"    空字段提示: {warned[0]}")

        # 只填端点，缺模型和Key
        warned.clear()
        page.endpoint_input.setText("https://api.test.com/v1")
        page.on_save()
        assert len(warned) > 0, "缺模型应触发警告"
        print(f"    缺模型提示: {warned[0]}")

        # 填端点和模型，缺Key
        warned.clear()
        page.model_input.setText("test-model")
        page.on_save()
        assert len(warned) > 0, "缺Key应触发警告"
        print(f"    缺Key提示: {warned[0]}")
    finally:
        QMessageBox.warning = original_warning

    print("    ✓ 表单校验正常")


def test_save_config():
    """测试保存配置到数据库"""
    print("[5] 测试保存配置到数据库...")
    get_app()
    page = SettingsPage()

    # 填写完整表单
    page.provider_combo.setCurrentText("DeepSeek")
    page.endpoint_input.setText("https://api.deepseek.com")
    page.model_input.setText("deepseek-chat")
    page.apikey_input.setText("sk-test-123456789")

    # Mock QMessageBox.information 避免弹窗
    original_info = QMessageBox.information
    QMessageBox.information = lambda *args: QMessageBox.StandardButton.Ok

    try:
        page.on_save()
    finally:
        QMessageBox.information = original_info

    # 从数据库读取验证
    config = get_ai_config()
    assert config["provider"] == "DeepSeek", f"provider不匹配: {config['provider']}"
    assert config["endpoint"] == "https://api.deepseek.com", f"endpoint不匹配"
    assert config["model"] == "deepseek-chat", f"model不匹配"
    assert config["api_key"] == "sk-test-123456789", f"api_key不匹配"
    assert config["configured"] is True, f"应已配置"

    print(f"    provider: {config['provider']}")
    print(f"    endpoint: {config['endpoint']}")
    print(f"    model: {config['model']}")
    print(f"    api_key: {config['api_key']}")
    print(f"    configured: {config['configured']}")
    print("    ✓ 保存配置成功")


def test_load_config():
    """测试加载已保存配置到表单"""
    print("[6] 测试加载已保存配置...")
    # 先保存一个配置
    save_ai_config("OpenAI", "https://api.openai.com/v1", "gpt-5.4-mini", "sk-loaded-test")

    get_app()
    # 重新创建页面，应自动加载配置
    page = SettingsPage()

    assert page.provider_combo.currentText() == "OpenAI", \
        f"应加载provider=OpenAI，实际={page.provider_combo.currentText()}"
    assert page.endpoint_input.text() == "https://api.openai.com/v1", \
        f"应加载endpoint，实际={page.endpoint_input.text()}"
    assert page.model_input.text() == "gpt-5.4-mini", \
        f"应加载model，实际={page.model_input.text()}"
    assert page.apikey_input.text() == "sk-loaded-test", \
        f"应加载api_key，实际={page.apikey_input.text()}"

    print(f"    加载 provider: {page.provider_combo.currentText()}")
    print(f"    加载 endpoint: {page.endpoint_input.text()}")
    print(f"    加载 model: {page.model_input.text()}")
    print(f"    加载 api_key: {page.apikey_input.text()}")
    print("    ✓ 加载配置正常")


def test_key_visibility_toggle():
    """测试API Key显示/隐藏切换"""
    print("[7] 测试API Key显示/隐藏...")
    get_app()
    page = SettingsPage()

    # 初始应为密码模式
    assert page.apikey_input.echoMode() == QLineEdit.EchoMode.Password, "初始应为密码模式"
    assert page.toggle_key_btn.text() == "显示", f"按钮应显示'显示'，实际={page.toggle_key_btn.text()}"

    # 点击切换为明文
    page.toggle_key_visibility()
    assert page.apikey_input.echoMode() == QLineEdit.EchoMode.Normal, "切换后应为明文模式"
    assert page.toggle_key_btn.text() == "隐藏", f"按钮应显示'隐藏'，实际={page.toggle_key_btn.text()}"

    # 再点击切回密码模式
    page.toggle_key_visibility()
    assert page.apikey_input.echoMode() == QLineEdit.EchoMode.Password, "再次切换应为密码模式"
    assert page.toggle_key_btn.text() == "显示"

    print("    密码模式 ↔ 明文模式 切换正常")
    print("    ✓ Key显示/隐藏正常")


def test_main_window_nav():
    """测试主窗口导航栏包含设置入口"""
    print("[8] 测试主窗口导航栏...")
    get_app()
    window = MainWindow()

    # 检查导航按钮组
    nav_group = window.nav_group
    assert nav_group is not None, "导航按钮组不应为空"

    # 应有5个导航按钮（首页/起卦/周易查询/历史记录/设置）
    button_ids = [nav_group.id(btn) for btn in nav_group.buttons()]
    assert len(button_ids) == 5, f"应有5个导航按钮，实际{len(button_ids)}: {button_ids}"
    assert 4 in button_ids, "缺少设置按钮(id=4)"

    # 检查页面栈
    pages = window.pages
    assert pages.count() == 5, f"应有5个页面，实际{pages.count()}"

    # 第5个页面（index=4）应为设置页
    settings_widget = pages.widget(4)
    assert isinstance(settings_widget, SettingsPage), "第5页应为SettingsPage"

    print(f"    导航按钮数: {len(button_ids)} (id: {button_ids})")
    print(f"    页面栈数: {pages.count()}")
    print(f"    设置页类型: {type(settings_widget).__name__}")
    print("    ✓ 主窗口导航栏正常")


def test_get_form_config():
    """测试表单配置获取方法"""
    print("[9] 测试 _get_form_config 方法...")
    get_app()
    page = SettingsPage()

    page.provider_combo.setCurrentText("Kimi (月之暗面)")
    page.endpoint_input.setText("https://api.moonshot.cn/v1")
    page.model_input.setText("moonshot-v1-8k")
    page.apikey_input.setText("sk-kimi-test")

    config = page._get_form_config()
    assert config["provider"] == "Kimi (月之暗面)"
    assert config["endpoint"] == "https://api.moonshot.cn/v1"
    assert config["model"] == "moonshot-v1-8k"
    assert config["api_key"] == "sk-kimi-test"
    assert config["configured"] is True, "字段完整时 configured 应为 True"

    print(f"    config: {config}")
    print("    ✓ 表单配置获取正常")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第三步测试：设置页UI")
    print("=" * 60)

    init_db()
    print("数据库初始化完成")

    # 备份当前AI配置，防止测试污染
    from scripts.test_utils import backup_ai_config, restore_ai_config
    backup = backup_ai_config()
    # 清理配置用于测试
    save_ai_config("", "", "", "")
    print("已备份并清理AI配置\n")

    tests = [
        test_page_instantiation,
        test_provider_combo,
        test_default_provider,
        test_model_placeholder,
        test_provider_auto_fill,
        test_form_validation_empty,
        test_save_config,
        test_load_config,
        test_key_visibility_toggle,
        test_main_window_nav,
        test_get_form_config,
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
