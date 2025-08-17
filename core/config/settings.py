"""
系统配置管理
基于Pydantic Settings的配置管理
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """系统配置类"""
    
    # 应用基础配置
    APP_NAME: str = "量化交易系统"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # 安全配置
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据库配置
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # 聚宽配置
    JQ_USERNAME: Optional[str] = Field(None, env="JQ_USERNAME")
    JQ_PASSWORD: Optional[str] = Field(None, env="JQ_PASSWORD")
    JQ_TOKEN: Optional[str] = Field(None, env="JQ_TOKEN")
    
    # 银河证券配置
    GALAXY_ACCOUNT: Optional[str] = Field(None, env="GALAXY_ACCOUNT")
    GALAXY_PASSWORD: Optional[str] = Field(None, env="GALAXY_PASSWORD")
    GALAXY_SERVER_URL: Optional[str] = Field(None, env="GALAXY_SERVER_URL")
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 交易配置
    MAX_POSITION_SIZE: float = Field(default=100000.0, env="MAX_POSITION_SIZE")
    MAX_SINGLE_POSITION: float = Field(default=20000.0, env="MAX_POSITION_SIZE")
    STOP_LOSS_RATIO: float = Field(default=0.05, env="STOP_LOSS_RATIO")
    TAKE_PROFIT_RATIO: float = Field(default=0.15, env="TAKE_PROFIT_RATIO")
    
    # 回测配置
    DEFAULT_INITIAL_CAPITAL: float = Field(default=1000000.0, env="DEFAULT_INITIAL_CAPITAL")
    DEFAULT_COMMISSION_RATE: float = Field(default=0.0003, env="DEFAULT_COMMISSION_RATE")
    DEFAULT_SLIPPAGE_RATE: float = Field(default=0.0001, env="DEFAULT_SLIPPAGE_RATE")
    
    # 策略配置
    DEFAULT_MA_SHORT_WINDOW: int = Field(default=5, env="DEFAULT_MA_SHORT_WINDOW")
    DEFAULT_MA_LONG_WINDOW: int = Field(default=20, env="DEFAULT_MA_LONG_WINDOW")
    DEFAULT_POSITION_SIZE: float = Field(default=0.1, env="DEFAULT_POSITION_SIZE")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # 缓存配置
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5分钟
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """解析允许的主机列表"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """验证数据库URL"""
        if not v:
            raise ValueError("数据库URL不能为空")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """验证密钥"""
        if not v or len(v) < 32:
            raise ValueError("密钥长度必须至少32位")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

# 导出配置
__all__ = ["settings"]
