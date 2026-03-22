# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - 视频下载器跨平台打包
"""

import sys
import os
from pathlib import Path

# 获取项目根目录（兼容 PyInstaller）
try:
    project_root = Path(__file__).resolve().parent.parent
except NameError:
    # PyInstaller 运行时 __file__ 可能不存在
    project_root = Path(sys.argv[1]).resolve().parent.parent if len(sys.argv) > 1 else Path.cwd()

block_cipher = None

a = Analysis(
    [str(project_root / 'backend' / 'main.py')],
    pathex=[str(project_root / 'backend')],
    binaries=[],
    datas=[
        (str(project_root / 'frontend' / 'dist'), 'frontend/dist'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.responses',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.websockets',
        'yt_dlp',
        'yt_dlp.utils',
        'yt_dlp.extractor',
        'websockets',
        'websockets.server',
        'websockets.client',
        'pydantic',
        'pydantic.dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
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
    name='VideoDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=sys.platform == 'win32',  # 只在 Windows 上使用 UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台以便调试（生产环境可改为 False）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可选：添加图标文件路径
)
