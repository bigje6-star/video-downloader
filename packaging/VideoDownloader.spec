# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - 视频下载器跨平台打包
"""

import sys
import os
from pathlib import Path

# 直接使用相对于当前工作目录的路径
# 当前工作目录应该是 backend，所以项目根是 ..
project_root = Path.cwd().parent
backend_dir = Path.cwd()

block_cipher = None

a = Analysis(
    [str(backend_dir / 'main.py')],
    pathex=[str(backend_dir)],
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
    upx=sys.platform == 'win32',
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
