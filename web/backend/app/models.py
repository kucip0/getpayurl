from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Integer, default=0, nullable=False)  # 1=管理员, 0=普通用户
    is_disabled = Column(Integer, default=0, nullable=False)  # 1=禁用, 0=正常
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PlatformConfig(Base):
    """平台配置表"""
    __tablename__ = "platform_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform_code = Column(String(50), nullable=False, index=True)
    shop_username = Column(String(100))
    shop_password = Column(String(255))
    product_urls = Column(Text)  # JSON数组
    cookies = Column(Text)  # JSON
    captcha_cookies = Column(Text)  # JSON - 验证码 Session 的 Cookies（解决多 worker 模式下的 Session 丢失问题）
    captcha_csrf_token = Column(String(500))  # 验证码 CSRF Token
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OrderLog(Base):
    """订单日志表"""
    __tablename__ = "order_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform_code = Column(String(50), nullable=False)
    product_url = Column(String(500))
    original_price = Column(DECIMAL(10, 2))
    new_price = Column(DECIMAL(10, 2))
    status = Column(String(20), default="pending")  # pending/processing/success/failed
    error_message = Column(Text)
    qr_code_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
