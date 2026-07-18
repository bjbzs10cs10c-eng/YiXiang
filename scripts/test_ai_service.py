"""测试 AI 服务层 - 验证 prompt 构建、URL 补全、异常处理

本测试不依赖真实网络调用，主要验证：
1. prompt 构建是否正确包含所有信息
2. URL 自动补全逻辑
3. 异常分类与友好提示
4. 未配置时的降级处理
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import init_db
from services.ai_service import (
    _build_prompt, _call_api, interpret_divination,
    test_connection, interpret_hexagram, AIError
)
from services.settings_service import save_ai_config, get_ai_config


# ---------- 测试数据 ----------

MOCK_RESULT = {
    "question": "事业发展如何？",
    "time": "2026-07-14 15:30:00",
    "original_hexagram": {
        "id": 1,
        "name": "乾",
        "binary_code": "111111",
        "upper_trigram": "乾",
        "lower_trigram": "乾",
        "gua_ci": "乾：元，亨，利，贞。",
        "xiang_ci": "天行健，君子以自强不息。",
        "tuan_ci": "大哉乾元，万物资始，乃统天。",
    },
    "original_yao_lines": [
        {"position": 1, "yao_name": "初九", "original_text": "潜龙勿用。", "translation": "龙潜伏着，不宜有所作为。"},
        {"position": 2, "yao_name": "九二", "original_text": "见龙在田，利见大人。", "translation": "龙出现在田野，利于见大人。"},
        {"position": 3, "yao_name": "九三", "original_text": "君子终日乾乾，夕惕若厉，无咎。", "translation": None},
        {"position": 9, "yao_name": "用九", "original_text": "见群龙无首，吉。", "translation": None},
    ],
    "moving_lines": [
        {"position": 1, "value": 6, "name": "老阴"},
    ],
    "moving_count": 1,
    "changed_hexagram": {
        "id": 44,
        "name": "姤",
        "gua_ci": "姤：女壮，勿用取女。",
    },
    "reading_text": "潜龙勿用。",
    "reading_source": "初九",
}

MOCK_HEXAGRAM = {
    "id": 1,
    "name": "乾",
    "binary_code": "111111",
    "upper_trigram": "乾",
    "lower_trigram": "乾",
    "gua_ci": "乾：元，亨，利，贞。",
    "tuan_ci": "大哉乾元，万物资始，乃统天。",
    "xiang_ci": "天行健，君子以自强不息。",
}

MOCK_YAO_LINES = [
    {"position": 1, "yao_name": "初九", "original_text": "潜龙勿用。", "translation": None},
    {"position": 2, "yao_name": "九二", "original_text": "见龙在田，利见大人。", "translation": None},
]


# ---------- 测试用例 ----------

def test_build_prompt_structure():
    """测试 prompt 结构正确"""
    print("[1] 测试 prompt 结构...")
    messages = _build_prompt(MOCK_RESULT)

    assert len(messages) == 2, f"应有2条消息，实际{len(messages)}"
    assert messages[0]["role"] == "system", "第一条应为system角色"
    assert messages[1]["role"] == "user", "第二条应为user角色"

    system_content = messages[0]["content"]
    assert "周易" in system_content, "系统提示应包含周易"
    assert "通俗易懂" in system_content, "系统提示应要求通俗易懂"

    print("    ✓ 消息结构正确（system + user）")


def test_prompt_contains_question():
    """测试 prompt 包含占问事项"""
    print("[2] 测试 prompt 包含占问事项...")
    messages = _build_prompt(MOCK_RESULT)
    user_content = messages[1]["content"]

    assert "事业发展如何" in user_content, "应包含占问问题"
    assert "2026-07-14" in user_content, "应包含时间"
    print("    ✓ 包含占问事项和时间")


def test_prompt_contains_hexagram_info():
    """测试 prompt 包含本卦信息"""
    print("[3] 测试 prompt 包含本卦信息...")
    messages = _build_prompt(MOCK_RESULT)
    content = messages[1]["content"]

    assert "乾" in content, "应包含本卦名"
    assert "天行健" in content, "应包含象辞"
    assert "元，亨，利，贞" in content, "应包含卦辞"
    assert "上卦：乾" in content, "应包含上卦"
    assert "下卦：乾" in content, "应包含下卦"
    print("    ✓ 包含本卦完整信息")


def test_prompt_contains_moving_lines():
    """测试 prompt 包含动爻信息"""
    print("[4] 测试 prompt 包含动爻信息...")
    messages = _build_prompt(MOCK_RESULT)
    content = messages[1]["content"]

    assert "动爻" in content, "应包含动爻标识"
    assert "第1爻" in content, "应包含动爻位置"
    assert "老阴" in content, "应包含动爻名称"
    assert "潜龙勿用" in content, "应包含动爻爻辞"
    assert "龙潜伏着" in content, "应包含爻辞译文"
    print("    ✓ 包含动爻信息及爻辞")


def test_prompt_contains_changed_hexagram():
    """测试 prompt 包含变卦信息"""
    print("[5] 测试 prompt 包含变卦信息...")
    messages = _build_prompt(MOCK_RESULT)
    content = messages[1]["content"]

    assert "变卦" in content, "应包含变卦标识"
    assert "姤" in content, "应包含变卦名"
    assert "女壮" in content, "应包含变卦卦辞"
    print("    ✓ 包含变卦信息")


def test_prompt_contains_reading():
    """测试 prompt 包含断卦依据"""
    print("[6] 测试 prompt 包含断卦依据...")
    messages = _build_prompt(MOCK_RESULT)
    content = messages[1]["content"]

    assert "断卦依据" in content, "应包含断卦依据标识"
    assert "初九" in content, "应包含断卦来源"
    print("    ✓ 包含断卦依据")


def test_prompt_static_hexagram():
    """测试静卦（无动爻）的 prompt"""
    print("[7] 测试静卦 prompt...")
    static_result = dict(MOCK_RESULT)
    static_result["moving_lines"] = []
    static_result["moving_count"] = 0
    static_result["changed_hexagram"] = None
    static_result["reading_text"] = "乾：元，亨，利，贞。"
    static_result["reading_source"] = "本卦卦辞"

    messages = _build_prompt(static_result)
    content = messages[1]["content"]

    assert "静卦" in content, "应标识为静卦"
    assert "变卦】无" in content, "应变卦为无"
    print("    ✓ 静卦 prompt 正确")


def test_url_completion():
    """测试 URL 自动补全逻辑"""
    print("[8] 测试 URL 自动补全...")
    import requests
    from services.ai_service import _call_api

    test_cases = [
        # DeepSeek 新端点（不带/v1）
        ("https://api.deepseek.com", "https://api.deepseek.com/chat/completions"),
        # DeepSeek 旧端点（带/v1，向后兼容）
        ("https://api.deepseek.com/v1", "https://api.deepseek.com/v1/chat/completions"),
        # OpenAI 标准端点
        ("https://api.openai.com/v1", "https://api.openai.com/v1/chat/completions"),
        # 带末尾斜杠
        ("https://api.openai.com/v1/", "https://api.openai.com/v1/chat/completions"),
        # 用户直接填了完整地址
        ("https://api.example.com/chat/completions", "https://api.example.com/chat/completions"),
        # 智谱GLM（/v4路径）
        ("https://open.bigmodel.cn/api/paas/v4", "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
    ]

    for input_endpoint, expected_url in test_cases:
        # Mock requests.post 捕获实际请求的 URL
        with patch("services.ai_service.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401  # 用401快速触发异常，不关心响应体
            mock_post.return_value = mock_response

            config = {
                "endpoint": input_endpoint,
                "model": "test-model",
                "api_key": "sk-test",
            }
            try:
                _call_api([{"role": "user", "content": "test"}], config)
            except AIError:
                pass

            actual_url = mock_post.call_args[0][0] if mock_post.call_args else None
            assert actual_url == expected_url, \
                f"URL补全错误: 输入={input_endpoint}, 期望={expected_url}, 实际={actual_url}"
            print(f"    {input_endpoint} → {actual_url}")

    print("    ✓ URL 补全正确")


def test_not_configured_error():
    """测试未配置时的错误提示"""
    print("[9] 测试未配置时错误...")
    # 先清除配置
    save_ai_config("", "", "", "")

    try:
        interpret_divination(MOCK_RESULT)
        assert False, "应抛出AIError"
    except AIError as e:
        assert e.error_type == "not_configured", f"错误类型应为not_configured，实际{e.error_type}"
        assert "设置" in e.message, "错误信息应提示去设置"
        print(f"    错误类型: {e.error_type}")
        print(f"    错误信息: {e.message}")
        print("    ✓ 未配置错误正常")


def test_connection_not_configured():
    """测试 test_connection 未配置时返回 False"""
    print("[10] 测试 test_connection 未配置...")
    save_ai_config("", "", "", "")
    success, msg = test_connection()
    assert success is False, "未配置时应返回False"
    assert "未配置" in msg, "应提示未配置"
    print(f"    返回: success={success}, msg={msg}")
    print("    ✓ 正常")


def test_timeout_error():
    """测试超时异常处理"""
    print("[11] 测试超时异常...")
    import requests

    with patch("services.ai_service.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("timeout")

        config = {"endpoint": "https://api.test.com/v1", "model": "test", "api_key": "sk-test"}
        try:
            _call_api([{"role": "user", "content": "test"}], config)
            assert False, "应抛出AIError"
        except AIError as e:
            assert e.error_type == "timeout", f"错误类型应为timeout，实际{e.error_type}"
            assert "超时" in e.message
            print(f"    错误类型: {e.error_type}, 信息: {e.message}")
            print("    ✓ 超时异常正常")


def test_connection_error():
    """测试连接错误异常处理"""
    print("[12] 测试连接错误异常...")
    import requests

    with patch("services.ai_service.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("conn error")

        config = {"endpoint": "https://api.test.com/v1", "model": "test", "api_key": "sk-test"}
        try:
            _call_api([{"role": "user", "content": "test"}], config)
            assert False, "应抛出AIError"
        except AIError as e:
            assert e.error_type == "connection"
            assert "连接" in e.message
            print(f"    错误类型: {e.error_type}, 信息: {e.message}")
            print("    ✓ 连接错误异常正常")


def test_auth_error():
    """测试401认证失败"""
    print("[13] 测试401认证失败...")
    with patch("services.ai_service.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        config = {"endpoint": "https://api.test.com/v1", "model": "test", "api_key": "sk-invalid"}
        try:
            _call_api([{"role": "user", "content": "test"}], config)
            assert False, "应抛出AIError"
        except AIError as e:
            assert e.error_type == "auth"
            assert "Key" in e.message
            print(f"    错误类型: {e.error_type}, 信息: {e.message}")
            print("    ✓ 认证失败异常正常")


def test_quota_error():
    """测试402/429额度不足"""
    print("[14] 测试额度不足异常...")
    for code in [402, 429]:
        with patch("services.ai_service.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = code
            mock_post.return_value = mock_response

            config = {"endpoint": "https://api.test.com/v1", "model": "test", "api_key": "sk-test"}
            try:
                _call_api([{"role": "user", "content": "test"}], config)
                assert False, f"HTTP {code}应抛出AIError"
            except AIError as e:
                assert e.error_type == "quota", f"HTTP {code}错误类型应为quota，实际{e.error_type}"
                assert "额度" in e.message
                print(f"    HTTP {code}: error_type={e.error_type}")

    print("    ✓ 额度不足异常正常")


def test_success_response():
    """测试成功响应解析"""
    print("[15] 测试成功响应解析...")
    with patch("services.ai_service.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "  这是AI的解读内容  "}}
            ]
        }
        mock_post.return_value = mock_response

        config = {"endpoint": "https://api.test.com/v1", "model": "test", "api_key": "sk-valid"}
        result = _call_api([{"role": "user", "content": "test"}], config)
        assert result == "这是AI的解读内容", f"应去除首尾空格，实际: '{result}'"
        print(f"    返回内容: {result}")
        print("    ✓ 成功响应解析正常")


def test_interpret_hexagram_prompt():
    """测试单卦解读函数"""
    print("[16] 测试 interpret_hexagram 函数...")
    with patch("services.ai_service.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "乾卦解读"}}]
        }
        mock_post.return_value = mock_response

        # 先配置好
        save_ai_config("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat", "sk-test")

        result = interpret_hexagram(MOCK_HEXAGRAM, MOCK_YAO_LINES)
        assert "乾卦解读" in result
        print(f"    返回: {result}")

        # 验证 prompt 内容
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        user_content = payload["messages"][1]["content"]
        assert "乾" in user_content, "应包含卦名"
        assert "天行健" in user_content, "应包含象辞"
        assert "潜龙勿用" in user_content, "应包含爻辞"
        print("    ✓ 单卦解读正常")


def main():
    print("=" * 60)
    print("易象 v2.0.0 第二步测试：AI 服务层")
    print("=" * 60)

    init_db()
    print("数据库初始化完成")

    # 备份当前AI配置，防止测试污染
    from scripts.test_utils import backup_ai_config, restore_ai_config
    backup = backup_ai_config()
    print("已备份当前AI配置\n")

    tests = [
        test_build_prompt_structure,
        test_prompt_contains_question,
        test_prompt_contains_hexagram_info,
        test_prompt_contains_moving_lines,
        test_prompt_contains_changed_hexagram,
        test_prompt_contains_reading,
        test_prompt_static_hexagram,
        test_url_completion,
        test_not_configured_error,
        test_connection_not_configured,
        test_timeout_error,
        test_connection_error,
        test_auth_error,
        test_quota_error,
        test_success_response,
        test_interpret_hexagram_prompt,
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
