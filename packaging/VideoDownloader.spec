# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - 视频下载器跨平台打包
"""

import sys
import os
from pathlib import Path
from PyInstaller.building.api import Analysis, PYZ, EXE
from PyInstaller.building.datastruct import TOC

# 使用环境变量或当前工作目录作为基准（GitHub Actions 中使用）
# 在 GitHub Actions 中，工作目录是项目根目录
if os.environ.get('GITHUB_WORKSPACE'):
    project_root = Path(os.environ['GITHUB_WORKSPACE'])
else:
    # 本地开发环境，使用脚本所在目录
    spec_dir = Path(__file__).parent
    project_root = spec_dir.parent

backend_dir = project_root / 'backend'
frontend_dist = project_root / 'frontend' / 'dist'

block_cipher = None

# macOS 下将前端文件放入 Resources 目录
if sys.platform == 'darwin':
    datas_path = (str(frontend_dist), 'Resources/frontend/dist')
else:
    datas_path = (str(frontend_dist), 'frontend/dist')

a = Analysis(
    [str(backend_dir / 'main.py')],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[datas_path],
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
