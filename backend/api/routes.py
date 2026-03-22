"""
API 路由
"""
import os
import uuid
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Request, WebSocket
from pydantic import BaseModel
from core.downloader import Downloader

router = APIRouter()

# 下载任务存储
download_tasks = {}
task_downloaders = {}

# 批量下载任务存储
batch_tasks = {}
batch_downloaders = {}

class ParseRequest(BaseModel):
    url: str
    cookies_from_browser: Optional[str] = None

class DownloadRequest(BaseModel):
    url: str
    format_id: str = 'best'
    filename_template: str = '%(title)s.%(ext)s'
    audio_format: Optional[str] = None
    cookies_from_browser: Optional[str] = None

class TaskControl(BaseModel):
    task_id: str

class BatchDownloadRequest(BaseModel):
    playlist_url: str
    selected_indices: List[int]
    format_id: str = 'best'
    filename_template: str = '%(title)s.%(ext)s'
    audio_format: Optional[str] = None
    concurrency: int = 1
    cookies_from_browser: Optional[str] = None

@router.post("/parse")
async def parse_url(req: ParseRequest, request: Request):
    """解析URL，获取视频信息"""
    download_dir = request.app.state.download_dir
    downloader = Downloader(download_dir)
    info = downloader.parse_url(req.url)
    return info

@router.post("/download")
async def start_download(req: DownloadRequest, request: Request):
    """开始下载"""
    task_id = str(uuid.uuid4())
    download_dir = request.app.state.download_dir
    cookies = req.cookies_from_browser or getattr(request.app.state, 'cookies_from_browser', None)
    
    def progress_callback(task_id: str, progress: dict):
        # 直接更新任务状态
        if task_id in download_tasks:
            download_tasks[task_id]['progress'] = progress
            download_tasks[task_id]['status'] = progress.get('status', 'downloading')
    
    downloader = Downloader(download_dir, progress_callback, cookies_from_browser=cookies)
    task_downloaders[task_id] = downloader
    
    # 创建任务记录
    download_tasks[task_id] = {
        'id': task_id,
        'url': req.url,
        'format_id': req.format_id,
        'audio_format': req.audio_format,
        'status': 'pending',
        'progress': {},
    }

    # 异步启动下载
    asyncio.create_task(
        downloader.download(task_id, req.url, req.format_id, req.filename_template, req.audio_format)
    )
    
    return {'task_id': task_id, 'status': 'started'}

@router.get("/tasks")
async def get_tasks():
    """获取所有任务"""
    return list(download_tasks.values())

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """获取单个任务"""
    return download_tasks.get(task_id, {'error': 'Task not found'})

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    if task_id in task_downloaders:
        task_downloaders[task_id].cancel_task(task_id)
        download_tasks[task_id]['status'] = 'cancelled'
        return {'status': 'cancelled'}
    return {'error': 'Task not found'}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    download_tasks.pop(task_id, None)
    task_downloaders.pop(task_id, None)
    return {'status': 'deleted'}

class SettingsRequest(BaseModel):
    download_dir: str
    cookies_from_browser: Optional[str] = None
    concurrency: int = 1

@router.get("/settings")
async def get_settings(request: Request):
    """获取设置"""
    return {
        'download_dir': request.app.state.download_dir,
        'cookies_from_browser': getattr(request.app.state, 'cookies_from_browser', None),
        'concurrency': getattr(request.app.state, 'concurrency', 1),
    }

@router.get("/settings/dirs")
async def get_common_dirs():
    """获取常用目录列表"""
    import platform
    home = os.path.expanduser("~")

    if platform.system() == "Windows":
        common_dirs = [
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Videos"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Music"),
        ]
    else:
        common_dirs = [
            os.path.join(home, "Downloads"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Videos"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Music"),
            "/tmp",
        ]
    # 只返回存在的目录
    return [d for d in common_dirs if os.path.exists(d)]

@router.post("/settings/select-dir")
async def select_directory(request: Request):
    """打开系统目录选择器"""
    import subprocess
    import platform

    system = platform.system()
    selected_dir = None

    if system == "Darwin":
        # macOS 使用 AppleScript 选择文件夹
        script = '''
        tell application "System Events"
            activate
            set chosenFolder to (choose folder with prompt "选择下载目录")
        end tell
        return POSIX path of chosenFolder
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                selected_dir = result.stdout.strip()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif system == "Windows":
        # Windows 使用 PowerShell 选择文件夹
        script = '''
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "选择下载目录"
        if ($dialog.ShowDialog() -eq "OK") {
            Write-Output $dialog.SelectedPath
        }
        '''
        try:
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                selected_dir = result.stdout.strip()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    else:
        # Linux 可以使用 zenity 或其他工具
        return {"status": "error", "message": "Linux 系统请手动输入路径"}

    if selected_dir:
        os.makedirs(selected_dir, exist_ok=True)
        request.app.state.download_dir = selected_dir
        return {"status": "ok", "download_dir": selected_dir}

    return {"status": "error", "message": "未选择目录"}

@router.post("/settings")
async def update_settings(req: SettingsRequest, request: Request):
    """更新设置"""
    # 验证目录是否存在，不存在则创建
    download_dir = os.path.expanduser(req.download_dir)
    os.makedirs(download_dir, exist_ok=True)
    request.app.state.download_dir = download_dir

    # 更新 Cookie 设置
    if req.cookies_from_browser is not None:
        request.app.state.cookies_from_browser = req.cookies_from_browser

    # 更新并发设置
    request.app.state.concurrency = req.concurrency

    return {
        'status': 'updated',
        'download_dir': download_dir,
        'cookies_from_browser': req.cookies_from_browser,
        'concurrency': req.concurrency,
    }

# ========== 批量下载任务 API ==========

@router.post("/download-batch")
async def start_batch_download(req: BatchDownloadRequest, request: Request):
    """开始批量下载"""
    batch_id = str(uuid.uuid4())
    download_dir = request.app.state.download_dir
    manager = request.app.state.manager

    # 存储视频任务ID到批量任务ID的映射
    video_to_batch = {}

    def progress_callback(task_id: str, progress: dict):
        # 处理批量任务进度
        if task_id in batch_tasks:
            # 这是批量进度更新
            batch_tasks[task_id]['progress'] = progress
            batch_tasks[task_id]['status'] = progress.get('status', 'downloading')
            # 同时更新video_tasks数据（如果提供）
            if 'video_tasks' in progress:
                batch_tasks[task_id]['video_tasks'] = progress['video_tasks']
        elif task_id in video_to_batch:
            # 这是单个视频进度更新
            related_batch_id = video_to_batch[task_id]
            if related_batch_id in batch_tasks:
                # 更新批量任务中的视频任务进度
                if 'video_tasks' not in batch_tasks[related_batch_id]:
                    batch_tasks[related_batch_id]['video_tasks'] = {}

                # 查找对应的视频任务并更新进度
                for video_id, video_task in batch_tasks[related_batch_id]['video_tasks'].items():
                    if video_task.get('task_id') == task_id:
                        video_task['progress'] = progress
                        video_task['status'] = progress.get('status', 'downloading')
                        break

    # 创建包装回调函数来跟踪视频任务
    def wrapped_progress_callback(task_id: str, progress: dict):
        # 记录视频任务ID到批量任务的映射
        if task_id != batch_id and progress.get('status') in ['downloading', 'finished', 'error']:
            # 通过检查 batch_tasks 来找到对应的批量任务
            for bid, btask in batch_tasks.items():
                if btask.get('id') == batch_id:
                    video_to_batch[task_id] = bid
                    break
        progress_callback(task_id, progress)

    downloader = Downloader(download_dir, wrapped_progress_callback, cookies_from_browser=cookies)
    batch_downloaders[batch_id] = downloader

    # 创建批量任务记录
    batch_tasks[batch_id] = {
        'id': batch_id,
        'playlist_url': req.playlist_url,
        'selected_indices': req.selected_indices,
        'format_id': req.format_id,
        'audio_format': req.audio_format,
        'status': 'pending',
        'progress': {},
        'video_tasks': {},
    }

    # 异步启动批量下载
    asyncio.create_task(
        downloader.download_batch(
            batch_id,
            req.playlist_url,
            req.selected_indices,
            req.format_id,
            req.audio_format,
            req.filename_template,
            req.concurrency
        )
    )

    return {'batch_id': batch_id, 'status': 'started'}

@router.get("/batch-tasks")
async def get_batch_tasks():
    """获取所有批量任务"""
    return list(batch_tasks.values())

@router.get("/batch-tasks/{batch_id}")
async def get_batch_task(batch_id: str):
    """获取单个批量任务"""
    return batch_tasks.get(batch_id, {'error': 'Batch task not found'})

@router.post("/batch-tasks/{batch_id}/cancel")
async def cancel_batch_task(batch_id: str):
    """取消批量任务"""
    if batch_id in batch_downloaders:
        batch_downloaders[batch_id].cancel_batch_task(batch_id)
        batch_tasks[batch_id]['status'] = 'cancelled'
        return {'status': 'cancelled'}
    return {'error': 'Batch task not found'}
