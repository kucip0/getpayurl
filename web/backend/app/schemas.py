from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# 认证相关
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class RegisterResponse(BaseModel):
    message: str
    user_id: int


# 平台相关
class PlatformInfo(BaseModel):
    code: str
    name: str
    host: str


class PlatformListResponse(BaseModel):
    platforms: list[PlatformInfo]


class ShopLoginRequest(BaseModel):
    username: str
    password: str


class ShopLoginResponse(BaseModel):
    success: bool
    message: str
    shop_name: Optional[str] = None
    balance: Optional[float] = None


# 订单相关
class PriceRequest(BaseModel):
    product_url: str


class PriceResponse(BaseModel):
    success: bool
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    original_price: Optional[float] = None
    stock: Optional[int] = None


class OrderRequest(BaseModel):
    product_url: str
    new_price: float


class ModifyPriceRequest(BaseModel):
    goods_id: str
    new_price: str


class ModifyPriceResponse(BaseModel):
    success: bool
    message: str
    goods_id: Optional[str] = None
    new_price: Optional[str] = None


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    qr_code_base64: Optional[str] = None
    payment_url: Optional[str] = None
    logs: list[str] = []


# 配置相关
class PlatformConfigResponse(BaseModel):
    shop_username: Optional[str] = None
    product_urls: list[str] = []
    has_login: bool = False


class PlatformConfigUpdate(BaseModel):
    shop_username: Optional[str] = None
    product_urls: list[str] = []


# 服务响应
class ServiceResponse(BaseModel):
    """服务层统一响应"""
    success: bool
    message: str
    data: Optional[dict] = None
    logs: list[str] = []
