# 视频下载器

基于 yt-dlp 的本地视频下载工具。

## 支持平台

- macOS
- Windows
- Linux

## 快速启动

### 最简单方式 (一键启动)

```bash
cd video-downloader
python start.py
```

首次运行会自动创建虚拟环境并安装依赖，之后可直接启动。

### 手动启动

### 1. 安装依赖

```bash
cd video-downloader/backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

python main.py
```

### 3. 访问

打开浏览器访问: http://localhost:8000

> **注意**: 如果端口 8000 被占用，可先关闭占用进程：`lsof -ti:8000 | xargs kill -9`

## 常见问题

### 端口被占用
```bash
# macOS/Linux: 查找并关闭占用 8000 端口的进程
lsof -ti:8000 | xargs kill -9

# Windows: 查找进程
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F
```

### 权限问题 (macOS/Linux)
如果遇到权限错误，可能需要使用虚拟环境：
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows 启动失败
如果 `python` 命令不可用，尝试：
```bash
py -3 main.py
# 或
python3 main.py
```

## 功能

- 支持 YouTube、B 站等数千个网站
- **批量下载** - 播放列表可批量选择视频下载
- 视频格式选择：
  - 最佳质量 (带音频)
  - 最佳视频 + 音频 (合并)
  - 1080p/720p/480p/360p MP4 (带音频)
  - MP4/WebM 格式 (自动选择)
- 音频提取 (MP3, M4A, WAV, AAC, FLAC, OGG)
- 实时下载进度
- 下载目录选择（支持系统目录选择器）
- 跨平台支持 (macOS/Windows/Linux)

## 依赖

- **Python**: 3.10+
- **Node.js**: 18+ (仅开发构建)
- **ffmpeg**: 提取音频需要安装

### 安装 ffmpeg

```bash
# macOS
brew install ffmpeg

# Windows (使用 winget)
winget install FFmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```
