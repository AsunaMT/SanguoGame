"""FastAPI 主入口"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import CORS_ORIGINS
from api.routes_setup import router as setup_router
from api.routes_court import router as court_router
from api.routes_world import router as world_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保存档目录存在
    os.makedirs("saves", exist_ok=True)
    yield


app = FastAPI(
    title="三国朝堂",
    description="赤壁前夕的朝堂策略游戏",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(setup_router)
app.include_router(court_router)
app.include_router(world_router)

# 前端静态文件
_FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(_FRONTEND):
    app.mount("/static", StaticFiles(directory=_FRONTEND), name="static")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(_FRONTEND, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok", "game": "三国朝堂"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
