"""易象（YiXiang）应用配置"""

import os
import sys


def _get_app_dir():
    """获取应用根目录，兼容 PyInstaller 打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后：exe 所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))


def _get_resource_dir():
    """获取资源目录（打包在 exe 内部的资源）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后：_MEIPASS 临时解压目录
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))


# 应用信息
APP_NAME = "易象"
APP_NAME_EN = "YiXiang"
VERSION = "2.1.0"

# AI服务商预设端点（OpenAI兼容格式）
# 端点填 base_url，程序自动补全 /chat/completions
# 模型名由用户自行填写，AI_PROVIDER_MODELS 提供推荐模型名作为参考
AI_PROVIDERS = {
    "DeepSeek": "https://api.deepseek.com",
    "通义千问": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "Kimi (月之暗面)": "https://api.moonshot.cn/v1",
    "智谱GLM": "https://open.bigmodel.cn/api/paas/v4",
    "OpenAI": "https://api.openai.com/v1",
    "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "Claude": "",  # Claude官方无OpenAI兼容端点，需填第三方代理地址
    "自定义": "",
}

# 各服务商推荐模型名（仅作参考提示，用户可填其他模型名）
# 来源：各官方API文档（2026-07核实）
AI_PROVIDER_MODELS = {
    "DeepSeek": "deepseek-v4-flash, deepseek-v4-pro",
    "通义千问": "qwen-plus, qwen-max, qwen-turbo",
    "Kimi (月之暗面)": "kimi-k2.6, kimi-k2.7-code",
    "智谱GLM": "glm-4.7-flash, glm-4-flash, glm-4",
    "OpenAI": "gpt-5.5, gpt-5.4, gpt-5.4-mini",
    "Gemini": "gemini-2.5-pro, gemini-2.5-flash",
    "Claude": "claude-sonnet-4, claude-opus-4 (需第三方代理)",
    "自定义": "",
}

# 默认服务商（首次打开设置页时选中）
AI_DEFAULT_PROVIDER = "DeepSeek"

# API Key 加密密钥（用于 settings 表中 Key 的简单加密，base64 + XOR）
# 注意：这不是真正的安全方案，仅防止肉眼直接读取
AI_KEY_SECRET = b"YiXiang_2026_Secret_Key"

# AI 调用默认参数
AI_DEFAULT_TIMEOUT = 60        # 请求超时（秒）
AI_DEFAULT_TEMPERATURE = 0.7   # 生成温度
AI_DEFAULT_MAX_TOKENS = 2000   # 最大返回 token 数

# settings 表中的 key 常量
SETTING_KEY_AI_PROVIDER = "ai_provider"       # 服务商名称
SETTING_KEY_AI_ENDPOINT = "ai_endpoint"       # API 端点
SETTING_KEY_AI_MODEL = "ai_model"             # 模型名
SETTING_KEY_AI_API_KEY = "ai_api_key"         # 加密后的 API Key

# 应用根目录
APP_DIR = _get_app_dir()

# 数据库（放在 exe 同级目录，用户可读写）
DATABASE_DIR = os.path.join(APP_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "yijing.db")

# 数据文件（打包在 exe 内部）
RESOURCE_DIR = _get_resource_dir()
DATA_DIR = os.path.join(RESOURCE_DIR, "data")
HEXAGRAMS_JSON = os.path.join(DATA_DIR, "hexagrams.json")
YAO_LINES_JSON = os.path.join(DATA_DIR, "yao_lines.json")
INTERPRETATIONS_JSON = os.path.join(DATA_DIR, "interpretations.json")

# 资源目录
RESOURCES_DIR = os.path.join(RESOURCE_DIR, "resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
IMAGES_DIR = os.path.join(RESOURCES_DIR, "images")

# 硬币图片
COIN_FRONT_IMG = os.path.join(IMAGES_DIR, "zheng.png")
COIN_BACK_IMG = os.path.join(IMAGES_DIR, "fan.png")

# 应用图标（用于 exe 和窗口图标）
APP_ICON = os.path.join(ICONS_DIR, "app.ico")

# 六爻规则
COIN_FRONT = 3  # 正面
COIN_BACK = 2   # 反面
YAO_OLD_YIN = 6     # 老阴
YAO_YOUNG_YANG = 7  # 少阳
YAO_YOUNG_YIN = 8   # 少阴
YAO_OLD_YANG = 9    # 老阳
