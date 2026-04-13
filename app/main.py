import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import BusinessError, business_error_handler
from app.db.database import init_db, async_session_factory
from app.db.seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：创建必要目录
    for dir_path in [settings.UPLOAD_DIR, settings.LOG_DIR, "data"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # 初始化数据库
    await init_db()

    # 填充种子数据
    async with async_session_factory() as session:
        await seed_data(session)

    yield


app = FastAPI(
    title="AI面试官系统",
    description="蓝领岗位AI面试系统MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
app.add_exception_handler(BusinessError, business_error_handler)

# 注册路由
from app.api.router import api_router
from app.api.ws import router as ws_router

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)  # WebSocket路由挂载在根路径


@app.get("/health")
async def health_check():
    return {"status": "ok"}
