"""
量化交易系统 v2.0.0
基于FastAPI的现代化量化交易平台

作者: liudong-work
版本: 2.0.0
日期: 2025-01-27
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

# 导入配置和路由
from core.config import settings
from core.database import init_db
from api.v1 import api_router as api_v1
from api.v2 import api_router as api_v2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动量化交易系统 v2.0.0...")
    
    # 初始化数据库
    await init_db()
    logger.info("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时执行
    logger.info("🔄 关闭量化交易系统...")

# 创建FastAPI应用
app = FastAPI(
    title="量化交易系统 v2.0.0",
    description="基于FastAPI的现代化量化交易平台",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 请求计时中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误", "error": str(exc)}
    )

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": time.time()
    }

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用量化交易系统 v2.0.0",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# 注册API路由
app.include_router(api_v1, prefix="/api/v1", tags=["v1"])
app.include_router(api_v2, prefix="/api/v2", tags=["v2"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
