"""
认证和授权模块
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
# from sqlalchemy.ext.asyncio import AsyncSession  # 暂时注释掉
import logging

from core.config import settings
# from core.database import get_db  # 暂时注释掉
# from models import User  # 暂时注释掉

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# 暂时注释掉需要数据库的函数
# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db)
# ) -> User:
#     """获取当前用户"""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="无法验证凭据",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     
#     # 这里应该从数据库获取用户
#     # 暂时返回模拟用户
#     user = User(
#         id=1,
#         username=username,
#         email="user@example.com",
#         hashed_password="",
#         is_active=True
#     )
#     
#     if user is None:
#         raise credentials_exception
#     return user

# async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
#     """获取当前活跃用户"""
#     if not current_user.is_active:
#         raise HTTPException(status_code=400, detail="用户未激活")
#     return current_user

# async def authenticate_user(username: str, password: str, db: AsyncSession) -> Optional[User]:
#     """验证用户"""
#     # 这里应该实现真实的用户验证逻辑
#     # 暂时返回模拟用户
#     if username == "admin" and password == "password":
#         return User(
#             id=1,
#             username=username,
#             email="admin@example.com",
#             hashed_password=get_password_hash(password),
#             is_active=True
#         )
#     return None
