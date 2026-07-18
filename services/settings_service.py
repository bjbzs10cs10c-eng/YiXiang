"""设置服务 - 读写 settings 表，含 API Key 的简单加解密"""

import base64
import sqlite3
from typing import Optional

from config import (DATABASE_PATH, AI_PROVIDERS, AI_KEY_SECRET,
                    SETTING_KEY_AI_PROVIDER, SETTING_KEY_AI_ENDPOINT,
                    SETTING_KEY_AI_MODEL, SETTING_KEY_AI_API_KEY)


def _get_db():
    return sqlite3.connect(DATABASE_PATH)


def get_setting(key: str) -> Optional[str]:
    """读取单个设置项

    Args:
        key: 设置项键名

    Returns:
        设置项值，不存在则返回 None
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_setting(key: str, value: str) -> None:
    """写入设置项（存在则更新）

    Args:
        key: 设置项键名
        value: 设置项值
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value)
    )
    conn.commit()
    conn.close()


# ---------- API Key 加解密 ----------

def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR 加密（对称）"""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_api_key(plain_key: str) -> str:
    """加密 API Key：XOR 后 base64 编码

    Args:
        plain_key: 明文 API Key

    Returns:
        加密后的字符串
    """
    if not plain_key:
        return ""
    data = plain_key.encode("utf-8")
    encrypted = _xor_bytes(data, AI_KEY_SECRET)
    return base64.b64encode(encrypted).decode("ascii")


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key

    Args:
        encrypted_key: 加密后的字符串

    Returns:
        明文 API Key
    """
    if not encrypted_key:
        return ""
    try:
        data = base64.b64decode(encrypted_key.encode("ascii"))
        decrypted = _xor_bytes(data, AI_KEY_SECRET)
        return decrypted.decode("utf-8")
    except Exception:
        return ""


# ---------- AI 配置整体读写 ----------

def get_ai_config() -> dict:
    """读取完整 AI 配置

    Returns:
        {
            "provider": str,      # 服务商名称
            "endpoint": str,      # API 端点
            "model": str,         # 模型名
            "api_key": str,       # 明文 API Key（已解密）
            "configured": bool,   # 是否已配置（endpoint + api_key + model 均非空）
        }
    """
    provider = get_setting(SETTING_KEY_AI_PROVIDER) or ""
    endpoint = get_setting(SETTING_KEY_AI_ENDPOINT) or ""
    model = get_setting(SETTING_KEY_AI_MODEL) or ""

    encrypted_key = get_setting(SETTING_KEY_AI_API_KEY) or ""
    api_key = decrypt_api_key(encrypted_key)

    configured = bool(endpoint and api_key and model)

    return {
        "provider": provider,
        "endpoint": endpoint,
        "model": model,
        "api_key": api_key,
        "configured": configured,
    }


def save_ai_config(provider: str, endpoint: str, model: str, api_key: str) -> None:
    """保存完整 AI 配置

    Args:
        provider: 服务商名称（如 "DeepSeek"）
        endpoint: API 端点
        model: 模型名
        api_key: 明文 API Key（函数内部会加密）
    """
    set_setting(SETTING_KEY_AI_PROVIDER, provider)
    set_setting(SETTING_KEY_AI_ENDPOINT, endpoint)
    set_setting(SETTING_KEY_AI_MODEL, model)
    set_setting(SETTING_KEY_AI_API_KEY, encrypt_api_key(api_key))


def get_endpoint_by_provider(provider: str) -> str:
    """根据服务商名称获取预设端点

    Args:
        provider: 服务商名称

    Returns:
        预设端点 URL，未找到返回空字符串
    """
    return AI_PROVIDERS.get(provider, "")


def is_ai_configured() -> bool:
    """快速判断 AI 是否已配置"""
    return get_ai_config()["configured"]
