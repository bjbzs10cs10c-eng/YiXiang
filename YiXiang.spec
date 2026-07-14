# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 易象"""

import os

block_cipher = None

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
    ],
    hiddenimports=[
        'core.coin',
        'core.yao',
        'core.hexagram',
        'core.transformation',
        'services.divination_service',
        'services.interpretation_service',
        'services.history_service',
        'controllers.divination_controller',
        'database.database',
        'scripts.init_database',
        'ui.hexagram_renderer',
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
    icon=None,  # 可后续添加 icon='resources/icons/app.ico'
)
