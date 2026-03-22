"""
视频下载器 - 整合版
基于 FastAPI + yt-dlp
"""
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from api import routes

# 下载输出目录
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")

# 获取基础目录和前端目录
# 支持开发环境和打包后环境
if getattr(sys, 'frozen', False):
    # 打包后的环境 - 使用 PyInstaller 的 _MEIPASS 临时目录
    BASE_DIR = Path(sys.executable).parent
    # 尝试多个可能的前端路径
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 解压后的临时目录
        FRONTEND_DIR = Path(sys._MEIPASS) / 'frontend' / 'dist'
    else:
        FRONTEND_DIR = BASE_DIR / 'frontend' / 'dist'

    # 如果上述路径不存在，尝试从 .app bundle 的 Resources 目录查找
    if not os.path.exists(str(FRONTEND_DIR)):
        FRONTEND_DIR = Path(os.path.dirname(sys.executable)) / 'Resources' / 'frontend' / 'dist'
else:
    # 开发环境
    BASE_DIR = Path(__file__).parent
    FRONTEND_DIR = BASE_DIR.parent / "frontend" / "dist"

FRONTEND_DIR = str(FRONTEND_DIR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建下载目录
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"="*40)
    print(f"  视频下载器")
    print(f"  访问地址: http://localhost:8000")
    print(f"  下载目录: {DOWNLOAD_DIR}")
    print(f"="*40)
    yield

app = FastAPI(
    title="视频下载器",
    description="基于 yt-dlp 的视频下载工具",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(routes.router, prefix="/api")

# 静态文件服务 - 挂载到 /assets 路径
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR + "/assets"), name="assets")

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_progress(self, task_id: str, progress: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "progress",
                    "task_id": task_id,
                    "data": progress
                })
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 前端入口
@app.get("/")
async def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return JSONResponse({
            "message": "前端未构建，请运行: cd frontend && npm run build",
            "download_dir": DOWNLOAD_DIR
        })

# 挂载 manager 到 app state
app.state.manager = manager
app.state.download_dir = DOWNLOAD_DIR

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
