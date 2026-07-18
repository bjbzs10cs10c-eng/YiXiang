"""AI 服务层 - 调用 OpenAI 兼容格式的 LLM API 进行占卜解读

支持任何兼容 OpenAI /v1/chat/completions 格式的服务商：
DeepSeek、通义千问、Kimi、智谱GLM、OpenAI、Gemini、Claude、自定义
"""

import json
import requests
from typing import Optional

from config import (AI_DEFAULT_TIMEOUT, AI_DEFAULT_TEMPERATURE,
                    AI_DEFAULT_MAX_TOKENS)
from services.settings_service import get_ai_config


class AIError(Exception):
    """AI 调用异常基类"""

    def __init__(self, message: str, error_type: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.error_type = error_type

    def __str__(self):
        return self.message


# ---------- Prompt 构建 ----------

def _build_prompt(result: dict) -> list:
    """根据占卜结果构建对话消息列表

    Args:
        result: start_divination 返回的完整结果字典

    Returns:
        OpenAI 格式的 messages 列表
    """
    orig = result.get("original_hexagram", {})
    changed = result.get("changed_hexagram")
    moving = result.get("moving_lines", [])
    reading_text = result.get("reading_text", "")
    reading_source = result.get("reading_source", "")

    # 系统提示词：设定 AI 角色
    system_prompt = (
        "你是一位精通《周易》的学者，擅长用通俗易懂的现代中文解读卦象。"
        "你的解读应当：\n"
        "1. 基于卦象、卦辞、爻辞等经典文本\n"
        "2. 结合占问者的具体问题进行分析\n"
        "3. 语言平实，避免晦涩文言，让普通人能理解\n"
        "4. 给出客观中正的解读，不夸大不恐吓\n"
        "5. 结构清晰，分为「卦象分析」「问题解读」「建议」三部分"
    )

    # 组装用户消息内容
    content = f"【占问事项】\n{result.get('question', '未填写')}\n\n"
    content += f"【占卜时间】\n{result.get('time', '未知')}\n\n"

    # 本卦信息
    content += f"【本卦】{orig.get('name', '未知')}\n"
    content += f"上卦：{orig.get('upper_trigram', '未知')}，下卦：{orig.get('lower_trigram', '未知')}\n"
    if orig.get("gua_ci"):
        content += f"卦辞：{orig['gua_ci']}\n"
    if orig.get("xiang_ci"):
        content += f"象辞：{orig['xiang_ci']}\n"

    # 动爻信息
    moving_count = result.get("moving_count", 0)
    if moving_count > 0:
        moving_str = "、".join([
            f"第{m['position']}爻（{m['name']}）" for m in moving
        ])
        content += f"\n【动爻】共{moving_count}个：{moving_str}\n"

        # 动爻爻辞
        orig_yao_lines = result.get("original_yao_lines", [])
        moving_positions = {m["position"] for m in moving}
        content += "动爻爻辞：\n"
        for yl in orig_yao_lines:
            if yl.get("position") in moving_positions and yl.get("position", 0) <= 6:
                content += f"  {yl.get('yao_name', '')}：{yl.get('original_text', '')}\n"
                if yl.get("translation"):
                    content += f"  译文：{yl['translation']}\n"
    else:
        content += "\n【动爻】无（静卦）\n"

    # 变卦信息
    if changed:
        content += f"\n【变卦】{changed.get('name', '未知')}\n"
        if changed.get("gua_ci"):
            content += f"变卦卦辞：{changed['gua_ci']}\n"
    else:
        content += "\n【变卦】无\n"

    # 断卦依据
    if reading_text and reading_source:
        content += f"\n【断卦依据】{reading_source}：{reading_text}\n"

    # 要求
    content += (
        "\n请根据以上卦象信息，为占问者解读。要求：\n"
        "1. 先分析本卦和变卦的整体含义\n"
        "2. 结合动爻爻辞说明吉凶趋势\n"
        "3. 针对占问者的具体问题给出解读\n"
        "4. 给出可行建议\n"
        "5. 全文使用现代中文，通俗易懂"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]


# ---------- HTTP 请求 ----------

def _call_api(messages: list, config: dict) -> str:
    """调用 OpenAI 兼容格式的 chat/completions 接口

    Args:
        messages: 消息列表
        config: AI 配置字典（含 endpoint, model, api_key）

    Returns:
        AI 返回的文本内容

    Raises:
        AIError: 调用失败
    """
    endpoint = config["endpoint"].rstrip("/")
    # 自动补全 /chat/completions 路径
    # 规则：预设端点已包含各自所需的路径前缀（如 /v1、/v4、/v1beta/openai）
    # 这里只统一补全 /chat/completions，不再自动添加 /v1
    if endpoint.endswith("/chat/completions"):
        url = endpoint
    else:
        url = endpoint + "/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": AI_DEFAULT_TEMPERATURE,
        "max_tokens": AI_DEFAULT_MAX_TOKENS,
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload,
            timeout=AI_DEFAULT_TIMEOUT
        )
    except requests.exceptions.Timeout:
        raise AIError(f"请求超时（{AI_DEFAULT_TIMEOUT}秒），请检查网络或稍后重试", "timeout")
    except requests.exceptions.ConnectionError:
        raise AIError("无法连接服务器，请检查网络或API地址是否正确", "connection")
    except requests.exceptions.RequestException as e:
        raise AIError(f"网络请求失败：{e}", "network")

    # 解析响应
    if response.status_code == 401:
        raise AIError("API Key 无效或已过期，请检查设置", "auth")
    elif response.status_code == 402 or response.status_code == 429:
        raise AIError("API 额度不足或请求过于频繁，请检查账户余额", "quota")
    elif response.status_code == 404:
        raise AIError(f"接口地址不存在（404），请检查API端点设置：{url}", "not_found")
    elif response.status_code >= 500:
        raise AIError(f"服务器内部错误（{response.status_code}），请稍后重试", "server")
    elif response.status_code != 200:
        # 其他错误，尝试解析错误信息
        err_detail = ""
        try:
            err_data = response.json()
            err_msg = err_data.get("error", {}).get("message", "")
            if err_msg:
                err_detail = err_msg
        except (json.JSONDecodeError, ValueError):
            err_detail = response.text[:200] if response.text else ""
        if err_detail:
            raise AIError(f"API返回错误（HTTP {response.status_code}）：{err_detail}", "api_error")
        raise AIError(f"请求失败（HTTP {response.status_code}），请求地址：{url}", "http_error")

    # 解析成功响应
    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise AIError(f"解析AI响应失败：{e}", "parse_error")


# ---------- 对外接口 ----------

def interpret_divination(result: dict) -> str:
    """对占卜结果进行 AI 解读

    Args:
        result: start_divination 返回的完整结果字典

    Returns:
        AI 解读文本

    Raises:
        AIError: 未配置AI或调用失败
    """
    # 检查配置
    config = get_ai_config()
    if not config["configured"]:
        raise AIError(
            "AI 尚未配置，请先到「设置」页面填写服务商、API地址、模型名和API Key",
            "not_configured"
        )

    # 构建 prompt
    messages = _build_prompt(result)

    # 调用 API
    return _call_api(messages, config)


def test_connection(config: dict = None) -> tuple:
    """测试 API 连接是否正常

    发送一条简短消息验证配置是否可用。

    Args:
        config: 可选，传入测试配置；不传则使用已保存的配置

    Returns:
        (success: bool, message: str) 成功返回True和AI回复，失败返回False和错误信息
    """
    if config is None:
        config = get_ai_config()

    if not config["configured"]:
        return False, "AI 尚未配置完整"

    messages = [
        {"role": "user", "content": "你好，请回复「连接成功」四个字"}
    ]

    try:
        reply = _call_api(messages, config)
        return True, reply
    except AIError as e:
        return False, e.message


def interpret_hexagram(hexagram: dict, yao_lines: list = None) -> str:
    """对单卦进行 AI 解读（用于卦库页面）

    Args:
        hexagram: 卦象信息字典
        yao_lines: 爻辞列表（可选）

    Returns:
        AI 解读文本

    Raises:
        AIError: 未配置AI或调用失败
    """
    config = get_ai_config()
    if not config["configured"]:
        raise AIError(
            "AI 尚未配置，请先到「设置」页面填写服务商、API地址、模型名和API Key",
            "not_configured"
        )

    # 构建单卦解读 prompt
    system_prompt = (
        "你是一位精通《周易》的学者，擅长用通俗易懂的现代中文解读卦象。"
        "请基于卦辞、爻辞等经典文本，为用户解读此卦的含义、象征和应用。"
    )

    content = f"【卦名】{hexagram.get('name', '未知')}\n"
    content += f"上卦：{hexagram.get('upper_trigram', '未知')}，下卦：{hexagram.get('lower_trigram', '未知')}\n"
    if hexagram.get("gua_ci"):
        content += f"卦辞：{hexagram['gua_ci']}\n"
    if hexagram.get("tuan_ci"):
        content += f"彖辞：{hexagram['tuan_ci']}\n"
    if hexagram.get("xiang_ci"):
        content += f"象辞：{hexagram['xiang_ci']}\n"

    if yao_lines:
        content += "\n【爻辞】\n"
        for yl in yao_lines:
            if yl.get("position", 0) <= 6:
                content += f"{yl.get('yao_name', '')}：{yl.get('original_text', '')}\n"

    content += "\n请解读此卦的整体含义、象征意义，以及在现代生活中的启示。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]

    return _call_api(messages, config)
