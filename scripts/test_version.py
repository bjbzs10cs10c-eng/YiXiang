"""测试第八步：版本号与打包配置

验证内容：
1. config.py 中 VERSION = "2.0.0"
2. AI_PROVIDERS 包含 8 家服务商
3. AI_DEFAULT_PROVIDER 为 DeepSeek
4. AI_PROVIDER_MODELS 与 AI_PROVIDERS 键一致
5. AI_KEY_SECRET 为 bytes 类型
6. settings 表 key 常量正确定义
7. requirements.txt 包含必要依赖
8. YiXiang.spec 包含新增模块
9. 关键模块可正常导入
10. main.py 入口正常
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_version():
    """测试版本号为 2.0.0"""
    print("[1] 测试版本号...")
    from config import VERSION
    assert VERSION == "2.0.0", f"版本号应为 2.0.0，实际={VERSION}"
    print(f"    VERSION = {VERSION}")
    print("    ✓ 版本号正确")


def test_ai_providers_count():
    """测试 AI_PROVIDERS 包含 8 家服务商"""
    print("[2] 测试 AI_PROVIDERS 服务商数量...")
    from config import AI_PROVIDERS
    assert len(AI_PROVIDERS) == 8, f"应有8家服务商，实际={len(AI_PROVIDERS)}"
    expected = {"DeepSeek", "通义千问", "Kimi (月之暗面)", "智谱GLM",
                "OpenAI", "Gemini", "Claude", "自定义"}
    assert set(AI_PROVIDERS.keys()) == expected, \
        f"服务商列表不匹配，实际={set(AI_PROVIDERS.keys())}"
    print(f"    服务商: {list(AI_PROVIDERS.keys())}")
    print("    ✓ 服务商列表正确")


def test_default_provider():
    """测试默认服务商为 DeepSeek"""
    print("[3] 测试默认服务商...")
    from config import AI_DEFAULT_PROVIDER
    assert AI_DEFAULT_PROVIDER == "DeepSeek", \
        f"默认服务商应为 DeepSeek，实际={AI_DEFAULT_PROVIDER}"
    print(f"    AI_DEFAULT_PROVIDER = {AI_DEFAULT_PROVIDER}")
    print("    ✓ 默认服务商正确")


def test_provider_models_match():
    """测试 AI_PROVIDER_MODELS 与 AI_PROVIDERS 键一致"""
    print("[4] 测试 AI_PROVIDER_MODELS 键一致...")
    from config import AI_PROVIDERS, AI_PROVIDER_MODELS
    assert set(AI_PROVIDERS.keys()) == set(AI_PROVIDER_MODELS.keys()), \
        f"键不一致: providers={set(AI_PROVIDERS.keys())}, models={set(AI_PROVIDER_MODELS.keys())}"
    print("    ✓ 服务商与模型映射键一致")


def test_key_secret_type():
    """测试 AI_KEY_SECRET 为 bytes 类型"""
    print("[5] 测试 AI_KEY_SECRET 类型...")
    from config import AI_KEY_SECRET
    assert isinstance(AI_KEY_SECRET, bytes), f"应为bytes，实际={type(AI_KEY_SECRET)}"
    assert len(AI_KEY_SECRET) > 0, "密钥不应为空"
    print(f"    AI_KEY_SECRET 类型: {type(AI_KEY_SECRET).__name__}, 长度: {len(AI_KEY_SECRET)}")
    print("    ✓ 密钥类型正确")


def test_settings_key_constants():
    """测试 settings 表 key 常量定义"""
    print("[6] 测试 settings 表 key 常量...")
    from config import (SETTING_KEY_AI_PROVIDER, SETTING_KEY_AI_ENDPOINT,
                        SETTING_KEY_AI_MODEL, SETTING_KEY_AI_API_KEY)
    assert SETTING_KEY_AI_PROVIDER == "ai_provider"
    assert SETTING_KEY_AI_ENDPOINT == "ai_endpoint"
    assert SETTING_KEY_AI_MODEL == "ai_model"
    assert SETTING_KEY_AI_API_KEY == "ai_api_key"
    print(f"    provider key: {SETTING_KEY_AI_PROVIDER}")
    print(f"    endpoint key: {SETTING_KEY_AI_ENDPOINT}")
    print(f"    model key: {SETTING_KEY_AI_MODEL}")
    print(f"    api_key key: {SETTING_KEY_AI_API_KEY}")
    print("    ✓ 常量定义正确")


def test_requirements_file():
    """测试 requirements.txt 包含必要依赖"""
    print("[7] 测试 requirements.txt...")
    req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt 应存在"

    with open(req_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PySide6" in content, "应有 PySide6"
    assert "requests" in content, "应有 requests（AI调用用）"
    assert "pyinstaller" in content, "应有 pyinstaller"
    # SQLAlchemy 已移除（项目用原生 sqlite3）
    assert "SQLAlchemy" not in content, "不应再有 SQLAlchemy（项目用原生 sqlite3）"
    print(f"    requirements.txt 内容:\n      {content.strip().replace(chr(10), chr(10) + '      ')}")
    print("    ✓ requirements.txt 正确")


def test_spec_file():
    """测试 YiXiang.spec 包含新增模块"""
    print("[8] 测试 YiXiang.spec...")
    spec_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "YiXiang.spec")
    assert os.path.exists(spec_path), "YiXiang.spec 应存在"

    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 验证新增模块
    required_modules = [
        "services.ai_service",
        "services.settings_service",
        "ui.settings_page",
        "ui.library_page",
        "ui.history_page",
        "ui.divination_page",
        "ui.home_page",
        "ui.main_window",
    ]
    for mod in required_modules:
        assert mod in content, f"spec 应包含 {mod}"

    # 验证数据文件
    assert "data/hexagrams.json" in content
    assert "data/yao_lines.json" in content
    assert "data/interpretations.json" in content
    assert "database/schema.sql" in content
    assert "resources/images/zheng.png" in content
    assert "resources/images/fan.png" in content

    print(f"    新增模块数: {len(required_modules)}")
    print("    ✓ YiXiang.spec 正确")


def test_imports():
    """测试关键模块可正常导入"""
    print("[9] 测试关键模块导入...")
    # 清理已导入的模块，重新导入
    import importlib
    modules_to_test = [
        "config",
        "services.ai_service",
        "services.settings_service",
        "services.history_service",
        "services.interpretation_service",
        "services.divination_service",
        "database.database",
        "ui.library_page",
        "ui.settings_page",
        "ui.history_page",
        "ui.divination_page",
        "ui.hexagram_renderer",
        "ui.main_window",
        "ui.home_page",
        "ui.styles",
        "core.coin",
        "core.yao",
        "core.hexagram",
        "core.transformation",
        "controllers.divination_controller",
    ]
    for mod_name in modules_to_test:
        try:
            importlib.import_module(mod_name)
        except Exception as e:
            raise AssertionError(f"导入 {mod_name} 失败: {e}")
    print(f"    成功导入 {len(modules_to_test)} 个模块")
    print("    ✓ 所有模块导入正常")


def test_main_entry():
    """测试 main.py 入口正常"""
    print("[10] 测试 main.py 入口...")
    main_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    assert os.path.exists(main_path), "main.py 应存在"

    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "from PySide6.QtWidgets import QApplication" in content
    assert "from ui.main_window import MainWindow" in content
    assert "from database.database import init_db" in content
    assert "init_db()" in content
    assert "QApplication" in content
    assert "MainWindow" in content
    print("    main.py 包含 QApplication 和 MainWindow 调用")
    print("    ✓ main.py 入口正常")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第八步测试：版本号与打包配置")
    print("=" * 60)

    tests = [
        test_version,
        test_ai_providers_count,
        test_default_provider,
        test_provider_models_match,
        test_key_secret_type,
        test_settings_key_constants,
        test_requirements_file,
        test_spec_file,
        test_imports,
        test_main_entry,
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

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
