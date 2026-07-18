"""测试工具 - 配置备份与恢复，防止测试污染生产数据"""

from services.settings_service import get_ai_config, save_ai_config


def backup_ai_config():
    """备份当前AI配置，返回配置字典"""
    return get_ai_config()


def restore_ai_config(backup: dict):
    """恢复AI配置"""
    save_ai_config(
        backup.get("provider", ""),
        backup.get("endpoint", ""),
        backup.get("model", ""),
        backup.get("api_key", ""),
    )
