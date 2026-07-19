# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 易象"""

import os

block_cipher = None

# 应用图标路径（用户放入 resources/icons/app.ico 后自动生效）
_icon_path = 'resources/icons/app.ico'
_icon_datas = []
_icon_param = None
if os.path.exists(_icon_path):
    _icon_datas = [(_icon_path, 'resources/icons')]
    _icon_param = _icon_path

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 打包数据文件（JSON 数据）
        ('data/hexagrams.json', 'data'),
        ('data/yao_lines.json', 'data'),
        ('data/interpretations.json', 'data'),
        # 打包建表SQL
        ('database/schema.sql', 'database'),
        ('resources/images/zheng.png', 'resources/images'),
        ('resources/images/fan.png', 'resources/images'),
    ] + _icon_datas,
    hiddenimports=[
        'core.coin',
        'core.yao',
        'core.hexagram',
        'core.transformation',
        'services.divination_service',
        'services.interpretation_service',
        'services.history_service',
        'services.ai_service',
        'services.settings_service',
        'controllers.divination_controller',
        'database.database',
        'scripts.init_database',
        'ui.hexagram_renderer',
        'ui.settings_page',
        'ui.library_page',
        'ui.history_page',
        'ui.divination_page',
        'ui.home_page',
        'ui.main_window',
        'ui.styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大模块
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'sqlalchemy',
        'openpyxl',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='易象',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon_param,  # 放入 resources/icons/app.ico 后自动生效
)
