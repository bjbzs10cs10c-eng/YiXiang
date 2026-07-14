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
VERSION = "1.0.2"

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

# 六爻规则
COIN_FRONT = 3  # 正面
COIN_BACK = 2   # 反面
YAO_OLD_YIN = 6     # 老阴
YAO_YOUNG_YANG = 7  # 少阳
YAO_YOUNG_YIN = 8   # 少阴
YAO_OLD_YANG = 9    # 老阳
