@echo off
REM Windows 构建脚本 - 视频下载器

setlocal enabledelayedexpansion

echo ========================================
echo   视频下载器 - Windows 构建脚本
echo ========================================
echo.

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

REM 检查 Python 版本
echo 📦 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python 版本: %PYTHON_VERSION%

REM 安装依赖
echo.
echo 📦 安装 Python 依赖...
cd backend
if not exist "venv" (
    python -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM 构建 React 前端
echo.
echo 🔨 构建前端...
cd "%PROJECT_ROOT%\frontend"
if not exist "node_modules" (
    npm install
)

call npm run build

REM 检查前端构建
if not exist "dist" (
    echo ❌ 错误: 前端构建失败，dist 目录不存在
    pause
    exit /b 1
)

REM 检查 FFmpeg
echo.
echo 🎬 检查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg 未安装
    echo 正在下载 FFmpeg...
    echo 请手动下载并安装 FFmpeg: https://ffmpeg.org/download.html
    echo 或使用: winget install FFmpeg
    pause
)

REM 使用 PyInstaller 打包
echo.
echo 🔨 使用 PyInstaller 打包...
cd "%PROJECT_ROOT%\backend"
pyinstaller "..\packaging\VideoDownloader.spec" --clean

REM 检查打包结果
if not exist "dist\VideoDownloader.exe" (
    echo ❌ 错误: PyInstaller 打包失败
    pause
    exit /b 1
)

REM 复制 FFmpeg 到 dist 目录（如果存在）
echo.
echo 📦 打包 FFmpeg...
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    for %%i in ('where ffmpeg') do set FFMPEG_PATH=%%i
    copy "!FFMPEG_PATH!" "dist\" >nul
    for %%i in ('where ffprobe') do set FFPROBE_PATH=%%i
    copy "!FFPROBE_PATH!" "dist\" >nul
    echo FFmpeg 已打包到 dist 目录
) else (
    echo ⚠️  FFmpeg 未找到，请手动放置 ffmpeg.exe 到 dist 目录
)

echo.
echo ========================================
echo ✅ 构建完成！
echo ========================================
echo 📍 输出目录: %PROJECT_ROOT%\backend\dist
echo 🚀 运行: cd %PROJECT_ROOT%\backend\dist && VideoDownloader.exe
echo.

pause
