"""
yt-dlp 下载器封装
"""
import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Callable, List
from yt_dlp import YoutubeDL

class Downloader:
    def __init__(self, download_dir: str, progress_callback: Optional[Callable] = None):
        self.download_dir = download_dir
        self.progress_callback = progress_callback
        self.active_tasks = {}
        self.batch_tasks = {}

    def parse_url(self, url: str) -> dict:
        """解析URL，获取视频信息或播放列表信息"""
        # 先使用 extract_flat 快速检测是否为播放列表
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                # 检测是否为播放列表
                if 'entries' in info:
                    # 调用播放列表解析方法
                    return self.parse_playlist(url)
                else:
                    # 单个视频
                    return self._format_video_info(info)
            except Exception as e:
                return {"error": str(e)}

    def parse_playlist(self, url: str) -> dict:
        """解析播放列表 URL，返回播放列表信息和视频数组"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # 不下载详细元数据，只获取基本信息
            'ignoreerrors': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)

                # 确保是播放列表
                if 'entries' not in info:
                    return {"error": "不是播放列表 URL"}

                videos = []
                for idx, entry in enumerate(info.get('entries', [])):
                    if entry is None:
                        continue
                    # 构建视频 URL
                    video_url = entry.get('url')
                    if not video_url and entry.get('id'):
                        video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"

                    videos.append({
                        'id': entry.get('id', ''),
                        'title': entry.get('title', 'Unknown'),
                        'url': video_url,
                        'duration': entry.get('duration', 0),
                        'thumbnail': entry.get('thumbnail', ''),
                        'uploader': entry.get('uploader', ''),
                        'uploader_id': entry.get('uploader_id', ''),
                        'index': idx + 1,
                        'selected': True,  # 默认选中
                    })

                return {
                    'is_playlist': True,
                    'id': info.get('id', ''),
                    'title': info.get('title', ''),
                    'uploader': info.get('uploader', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'video_count': len(videos),
                    'videos': videos,
                }
            except Exception as e:
                return {"error": str(e)}

    def _format_video_info(self, info: dict) -> dict:
        """格式化视频信息"""
        formats = []
        if 'formats' in info:
            for f in info['formats']:
                if f.get('url'):
                    # 判断是否有音频 (acodec 不为 'none')
                    has_audio = f.get('acodec') and f.get('acodec') != 'none'
                    # 获取分辨率
                    res = f.get('resolution', '')
                    # 跳过纯音频但不是音频提取模式的情况
                    if res == 'audio only' and not has_audio:
                        continue
                    formats.append({
                        'format_id': f.get('format_id', ''),
                        'ext': f.get('ext', ''),
                        'resolution': res,
                        'filesize': f.get('filesize', 0) or f.get('filesize_approx', 0),
                        'note': f.get('format_note', ''),
                        'has_audio': has_audio,
                    })

        # 排序格式 (处理 None 值)
        formats.sort(key=lambda x: x.get('filesize') or 0, reverse=True)

        # 简化格式列表，只保留不同质量的（优先保留带音频的）
        seen_resolutions = set()
        unique_formats = []
        for f in formats:
            res = f.get('resolution', '') or ''
            # 跳过空分辨率
            if not res or res == 'audio only':
                continue
            # 如果已存在同分辨率，保留带音频的
            if res in seen_resolutions:
                continue
            seen_resolutions.add(res)
            unique_formats.append(f)

        return {
            'id': info.get('id', ''),
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'thumbnail': info.get('thumbnail', ''),
            'uploader': info.get('uploader', ''),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'upload_date': info.get('upload_date', ''),
            'formats': unique_formats[:10],
        }

    async def download(
        self,
        task_id: str,
        url: str,
        format_id: str = 'best',
        filename_template: str = '%(title)s.%(ext)s',
        audio_format: str = None
    ) -> dict:
        """下载视频或音频"""

        def progress_hook(d):
            if d['status'] == 'downloading':
                if self.progress_callback:
                    self.progress_callback(task_id, {
                        'status': 'downloading',
                        'filename': d.get('filename', ''),
                        'percent': d.get('_percent_str', '0%'),
                        'speed': d.get('_speed_str', ''),
                        'eta': d.get('_eta_str', ''),
                        'total_bytes': d.get('total_bytes', 0),
                        'downloaded_bytes': d.get('downloaded_bytes', 0),
                    })
            elif d['status'] == 'finished':
                if self.progress_callback:
                    self.progress_callback(task_id, {
                        'status': 'finished',
                        'filename': d.get('filename', ''),
                    })

        # 音频提取模式
        if audio_format and audio_format in ['mp3', 'm4a', 'wav', 'aac', 'flac', 'ogg']:
            output_path = os.path.join(self.download_dir, '%(title)s.%(ext)s')
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'progress_hooks': [progress_hook],
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': '192',
                }],
            }
        else:
            output_path = os.path.join(self.download_dir, filename_template)

            # 确定下载格式
            fmt = format_id
            if fmt == 'best':
                # 最佳质量 + 最佳音频
                fmt = 'bestvideo+bestaudio'
            elif fmt == 'bestvideo+bestaudio' or '+' in fmt:
                # 已经是组合格式
                pass
            elif fmt == 'audio_only':
                # 仅音频模式（备用）
                fmt = 'bestaudio/best'
            elif fmt.isdigit():
                # 用户选择了具体格式ID，添加音频
                fmt = f'{fmt}+bestaudio'

            ydl_opts = {
                'format': fmt,
                'outtmpl': output_path,
                'progress_hooks': [progress_hook],
                'quiet': True,
                # 合并音视频
                'merge_output_format': 'mp4',
            }

        self.active_tasks[task_id] = True

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._download_sync, ydl_opts, url)
            return {'status': 'completed', 'task_id': task_id}
        except Exception as e:
            return {'status': 'error', 'task_id': task_id, 'error': str(e)}
        finally:
            self.active_tasks.pop(task_id, None)

    async def download_batch(
        self,
        batch_id: str,
        playlist_url: str,
        selected_indices: List[int],
        format_id: str = 'best',
        audio_format: str = None,
        filename_template: str = '%(title)s.%(ext)s',
        concurrency: int = 1
    ) -> dict:
        """批量下载播放列表视频，支持并发控制"""

        # 1. 解析播放列表
        playlist_info = self.parse_playlist(playlist_url)
        if 'error' in playlist_info:
            return {'status': 'error', 'error': playlist_info['error']}

        # 2. 筛选选中的视频
        selected_videos = [
            v for v in playlist_info['videos']
            if v['index'] in selected_indices
        ]

        if not selected_videos:
            return {'status': 'error', 'error': '没有选中的视频'}

        # 3. 初始化批量任务状态
        self.batch_tasks[batch_id] = {
            'batch_id': batch_id,
            'playlist_url': playlist_url,
            'total_videos': len(selected_videos),
            'completed_videos': 0,
            'failed_videos': 0,
            'status': 'downloading',
            'video_tasks': {},
            'start_time': datetime.now().isoformat(),
            'active': True,
        }

        # 4. 根据并发数选择下载方式
        if concurrency == 1:
            # 顺序下载
            for video in selected_videos:
                if not self.batch_tasks.get(batch_id, {}).get('active', True):
                    break

                task_id = str(uuid.uuid4())
                self.batch_tasks[batch_id]['video_tasks'][video['id']] = {
                    'task_id': task_id,
                    'status': 'pending',
                    'title': video['title'],
                    'index': video['index'],
                }

                # 推送批量进度更新（包含video_tasks数据）
                if self.progress_callback:
                    self.progress_callback(batch_id, {
                        'status': 'batch_progress',
                        'current_video_title': video['title'],
                        'current_video_index': video['index'],
                        'completed': self.batch_tasks[batch_id]['completed_videos'],
                        'total': self.batch_tasks[batch_id]['total_videos'],
                        'video_tasks': self.batch_tasks[batch_id]['video_tasks'],
                    })

                # 下载单个视频
                result = await self.download(
                    task_id,
                    video['url'],
                    format_id,
                    filename_template,
                    audio_format
                )

                # 更新批量任务状态
                if result['status'] == 'completed':
                    self.batch_tasks[batch_id]['completed_videos'] += 1
                    self.batch_tasks[batch_id]['video_tasks'][video['id']]['status'] = 'completed'
                else:
                    self.batch_tasks[batch_id]['failed_videos'] += 1
                    self.batch_tasks[batch_id]['video_tasks'][video['id']]['status'] = 'failed'
        else:
            # 并发下载
            semaphore = asyncio.Semaphore(concurrency)
            async def download_video(video):
                if not self.batch_tasks.get(batch_id, {}).get('active', True):
                    return None

                async with semaphore:
                    task_id = str(uuid.uuid4())
                    self.batch_tasks[batch_id]['video_tasks'][video['id']] = {
                        'task_id': task_id,
                        'status': 'pending',
                        'title': video['title'],
                        'index': video['index'],
                    }

                    # 推送批量进度更新（包含video_tasks数据）
                    if self.progress_callback:
                        self.progress_callback(batch_id, {
                            'status': 'batch_progress',
                            'current_video_title': video['title'],
                            'current_video_index': video['index'],
                            'completed': self.batch_tasks[batch_id]['completed_videos'],
                            'total': self.batch_tasks[batch_id]['total_videos'],
                            'video_tasks': self.batch_tasks[batch_id]['video_tasks'],
                        })

                    # 下载单个视频
                    result = await self.download(
                        task_id,
                        video['url'],
                        format_id,
                        filename_template,
                        audio_format
                    )

                    # 更新批量任务状态
                    if result['status'] == 'completed':
                        self.batch_tasks[batch_id]['completed_videos'] += 1
                        self.batch_tasks[batch_id]['video_tasks'][video['id']]['status'] = 'completed'
                    else:
                        self.batch_tasks[batch_id]['failed_videos'] += 1
                        self.batch_tasks[batch_id]['video_tasks'][video['id']]['status'] = 'failed'

                    return result

            # 创建并发任务
            tasks = [download_video(video) for video in selected_videos]
            await asyncio.gather(*tasks, return_exceptions=True)

        # 5. 更新最终状态
        batch_task = self.batch_tasks[batch_id]
        if batch_task['failed_videos'] == 0:
            batch_task['status'] = 'completed'
        elif batch_task['completed_videos'] > 0:
            batch_task['status'] = 'partial_failed'
        else:
            batch_task['status'] = 'failed'

        # 推送最终状态
        if self.progress_callback:
            self.progress_callback(batch_id, {
                'status': 'batch_finished',
                'completed': batch_task['completed_videos'],
                'failed': batch_task['failed_videos'],
                'total': batch_task['total_videos'],
            })

        return {
            'status': batch_task['status'],
            'batch_id': batch_id,
            'completed': batch_task['completed_videos'],
            'failed': batch_task['failed_videos'],
            'total': batch_task['total_videos'],
        }

    def cancel_batch_task(self, batch_id: str):
        """取消批量任务"""
        if batch_id in self.batch_tasks:
            self.batch_tasks[batch_id]['active'] = False
            # 同时取消所有活跃的子任务
            for video_id, task_id in self.batch_tasks[batch_id]['video_tasks'].items():
                if task_id in self.active_tasks:
                    self.active_tasks[task_id] = False

    def _download_sync(self, ydl_opts: dict, url: str):
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def cancel_task(self, task_id: str):
        """取消任务"""
        self.active_tasks[task_id] = False
