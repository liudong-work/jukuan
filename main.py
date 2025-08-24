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
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import logging
from contextlib import asynccontextmanager
import os

# 导入配置和路由
from core.config import settings
# from core.database import init_db  # 暂时注释掉
from api.v1 import api_router as api_v1
from api.v2 import api_router as api_v2

# 配置日志
logging.basicConfig(level=logging.INFO)

# 版本信息
__version__ = "2.0.0"
__author__ = "liudong-work"
__date__ = "2025-01-27"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logging.info("🚀 启动量化交易系统 v2.0.0...")
    
    # 暂时注释掉数据库初始化
    # await init_db()
    # logging.info("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时执行
    logging.info("🔄 关闭量化交易系统...")

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

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板配置
templates = Jinja2Templates(directory="templates")

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
    logging.error(f"全局异常: {exc}")
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

# 根路径 - 返回Web界面
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径 - 返回Web界面"""
    return templates.TemplateResponse("index.html", {"request": request})

# Web界面路由
@app.get("/web", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Web界面"""
    return templates.TemplateResponse("index.html", {"request": request})

# 聚宽演示页面
@app.get("/jq-demo", response_class=HTMLResponse)
async def jq_demo(request: Request):
    """聚宽演示页面"""
    return templates.TemplateResponse("jq_simple.html", {"request": request})

# 股票列表页面
@app.get("/stock-table", response_class=HTMLResponse)
async def stock_table(request: Request):
    """股票列表页面"""
    return templates.TemplateResponse("stock_table.html", {"request": request})

@app.get("/trading", response_class=HTMLResponse)
async def trading_page(request: Request):
    """交易管理页面"""
    return templates.TemplateResponse("trading.html", {"request": request})

@app.get("/strategy", response_class=HTMLResponse)
async def strategy_page(request: Request):
    """策略管理页面"""
    return templates.TemplateResponse("strategy.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """实时监控仪表板"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/smart-assistant", response_class=HTMLResponse)
async def smart_assistant_page(request: Request):
    """智能交易助手页面"""
    return templates.TemplateResponse("smart_assistant.html", {"request": request})

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """分析页面"""
    return templates.TemplateResponse("analysis.html", {"request": request})

@app.get("/realtime-data", response_class=HTMLResponse)
async def realtime_data_page(request: Request):
    """实时数据页面"""
    return templates.TemplateResponse("realtime_data.html", {"request": request})

@app.get("/ml-strategy", response_class=HTMLResponse)
async def ml_strategy_page(request: Request):
    """ML策略页面"""
    return templates.TemplateResponse("ml_strategy.html", {"request": request})

@app.get("/auto-trading", response_class=HTMLResponse)
async def auto_trading_page(request: Request):
    """自动交易页面"""
    return templates.TemplateResponse("auto_trading.html", {"request": request})

# 系统信息
@app.get("/system")
async def system_info():
    """系统信息"""
    return {
        "name": "量化交易系统",
        "version": "2.0.0",
        "status": "running",
        "uptime": time.time(),
        "features": [
            "FastAPI框架",
            "异步处理",
            "实时数据",
            "自动交易",
            "策略回测",
            "风险管理"
        ]
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
