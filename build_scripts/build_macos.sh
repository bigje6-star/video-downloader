#!/bin/bash
# macOS 构建脚本 - 视频下载器

set -e

echo "🚀 开始构建 macOS 版本..."

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📦 Python 版本: $PYTHON_VERSION"

# 检查 Python 版本是否 >= 3.10
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ 错误: 需要 Python 3.10 或更高版本"
    exit 1
fi

# 安装依赖
echo "📦 安装 Python 依赖..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 构建 React 前端
echo "🔨 构建前端..."
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build

# 检查前端构建
if [ ! -d "dist" ]; then
    echo "❌ 错误: 前端构建失败，dist 目录不存在"
    exit 1
fi

# 检查并安装 FFmpeg
echo "🎬 检查 FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg 未安装，正在安装..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ 错误: 请先安装 Homebrew: https://brew.sh"
        exit 1
    fi
fi

# 使用 PyInstaller 打包
echo "🔨 使用 PyInstaller 打包..."
cd "$PROJECT_ROOT/backend"
pyinstaller "../packaging/VideoDownloader.spec" --clean

# 检查打包结果
if [ ! -f "dist/VideoDownloader" ]; then
    echo "❌ 错误: PyInstaller 打包失败"
    exit 1
fi

# 复制 FFmpeg 到 dist 目录
echo "📦 打包 FFmpeg..."
cd dist
cp "$(which ffmpeg)" .
cp "$(which ffprobe)" .

# 创建应用程序包（可选）
# 如果想制作 .app 包，可以在这里添加相关命令

echo "✅ 构建完成！"
echo "📍 输出目录: $PROJECT_ROOT/backend/dist"
echo "🚀 运行: cd $PROJECT_ROOT/backend/dist && ./VideoDownloader"

# 询问是否打开应用
read -p "是否立即运行应用？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_ROOT/backend/dist"
    ./VideoDownloader
fi
