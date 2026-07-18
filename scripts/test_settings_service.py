"""测试设置服务 - 验证第一步配置基础设施"""

import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db
from services.settings_service import (
    get_setting, set_setting,
    encrypt_api_key, decrypt_api_key,
    get_ai_config, save_ai_config,
    get_endpoint_by_provider, is_ai_configured,
)
from config import AI_PROVIDERS, VERSION


def test_version():
    """测试版本号"""
    print(f"[1] 版本号: {VERSION}")
    assert VERSION == "2.0.0", f"版本号应为2.0.0，实际为{VERSION}"
    print("    ✓ 版本号正确")


def test_ai_providers():
    """测试AI服务商预设"""
    print(f"[2] AI服务商预设列表 ({len(AI_PROVIDERS)} 个):")
    for name, url in AI_PROVIDERS.items():
        print(f"    - {name}: {url}")

    assert "DeepSeek" in AI_PROVIDERS, "缺少 DeepSeek"
    assert "Gemini" in AI_PROVIDERS, "缺少 Gemini"
    assert "Claude" in AI_PROVIDERS, "缺少 Claude"
    assert "自定义" in AI_PROVIDERS, "缺少 自定义"
    assert AI_PROVIDERS["自定义"] == "", "自定义端点应为空"
    print("    ✓ 服务商列表完整")


def test_basic_setting():
    """测试基础读写"""
    print("[3] 测试基础读写...")
    set_setting("test_key", "test_value")
    val = get_setting("test_key")
    assert val == "test_value", f"读取值应为test_value，实际为{val}"

    # 测试更新
    set_setting("test_key", "updated_value")
    val = get_setting("test_key")
    assert val == "updated_value", f"更新后应为updated_value，实际为{val}"

    # 测试不存在的key
    val = get_setting("nonexistent_key")
    assert val is None, f"不存在的key应返回None，实际为{val}"
    print("    ✓ 基础读写正常")


def test_key_encryption():
    """测试API Key加解密"""
    print("[4] 测试API Key加解密...")
    test_keys = [
        "sk-1234567890abcdef",
        "sk-deepseek-xxxxxxxxxxxxxxxxxxxx",
        "",
        "中文key测试_!@#$%^&*()",
    ]

    for plain in test_keys:
        encrypted = encrypt_api_key(plain)
        decrypted = decrypt_api_key(encrypted)
        if plain == "":
            assert decrypted == "", f"空字符串解密应返回空，实际为{decrypted}"
        else:
            assert decrypted == plain, f"解密失败: 原文={plain}, 解密={decrypted}"
            assert encrypted != plain, f"加密后不应与原文相同"
        print(f"    明文: {plain[:20]}{'...' if len(plain)>20 else ''} → 加密: {encrypted[:30]}... → 解密: {decrypted[:20]}{'...' if len(decrypted)>20 else ''}")

    print("    ✓ 加解密正常")


def test_ai_config():
    """测试AI配置整体读写"""
    print("[5] 测试AI配置整体读写...")

    # 初始状态
    config = get_ai_config()
    print(f"    初始状态: configured={config['configured']}")

    # 保存配置
    test_provider = "DeepSeek"
    test_endpoint = "https://api.deepseek.com/v1"
    test_model = "deepseek-chat"
    test_key = "sk-test-1234567890abcdef"

    save_ai_config(test_provider, test_endpoint, test_model, test_key)
    print(f"    已保存: provider={test_provider}, model={test_model}")

    # 读取验证
    config = get_ai_config()
    assert config["provider"] == test_provider, f"provider不匹配"
    assert config["endpoint"] == test_endpoint, f"endpoint不匹配"
    assert config["model"] == test_model, f"model不匹配"
    assert config["api_key"] == test_key, f"api_key解密后不匹配"
    assert config["configured"] is True, f"应已配置"

    print(f"    读取验证: provider={config['provider']}, model={config['model']}, configured={config['configured']}")
    print(f"    API Key 解密: {config['api_key']}")
    print("    ✓ AI配置读写正常")


def test_is_configured():
    """测试is_ai_configured"""
    print("[6] 测试is_ai_configured...")
    result = is_ai_configured()
    assert result is True, "应返回True（上一步已保存配置）"
    print(f"    is_ai_configured() = {result}")
    print("    ✓ 正常")


def test_get_endpoint():
    """测试预设端点查询"""
    print("[7] 测试预设端点查询...")
    for provider in ["DeepSeek", "OpenAI", "Gemini", "Claude", "自定义", "不存在的"]:
        endpoint = get_endpoint_by_provider(provider)
        print(f"    {provider} → {endpoint}")
    assert get_endpoint_by_provider("DeepSeek") == "https://api.deepseek.com"
    assert get_endpoint_by_provider("Claude") == "", "Claude无官方OpenAI兼容端点，应为空"
    assert get_endpoint_by_provider("不存在的") == ""
    print("    ✓ 正常")


def test_db_storage():
    """验证数据库中存储的是加密后的Key"""
    print("[8] 验证数据库存储的是加密Key...")
    import sqlite3
    from config import DATABASE_PATH, SETTING_KEY_AI_API_KEY

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (SETTING_KEY_AI_API_KEY,))
    row = cursor.fetchone()
    conn.close()

    stored_value = row[0] if row else None
    print(f"    数据库中存储的值: {stored_value}")
    assert stored_value is not None, "数据库中应存在加密Key"
    assert stored_value != "sk-test-1234567890abcdef", "数据库中不应存储明文Key"
    assert "sk-test" not in stored_value, "加密后不应包含明文片段"
    print("    ✓ 数据库存储的是加密内容")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第一步测试：配置基础设施")
    print("=" * 60)

    # 初始化数据库
    init_db()
    print("数据库初始化完成")

    # 备份当前AI配置，防止测试污染
    from scripts.test_utils import backup_ai_config, restore_ai_config
    backup = backup_ai_config()
    print("已备份当前AI配置\n")

    tests = [
        test_version,
        test_ai_providers,
        test_basic_setting,
        test_key_encryption,
        test_ai_config,
        test_is_configured,
        test_get_endpoint,
        test_db_storage,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"    ✗ 失败: {e}")
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
