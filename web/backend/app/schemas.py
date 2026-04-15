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


# 订单查询相关
class OrderItem(BaseModel):
    """单个订单数据项"""
    order_no: str                    # 订单号 (如 HOU26041513209L4HU)
    order_type: str                  # 订单类型 (普通订单/对接订单/跨平台订单)
    product_name: str                # 商品名称
    supplier: str = ""               # 供货商 (可能为空)
    payment_method: str              # 支付方式 (支付宝扫码等)
    total_price: str                 # 总价
    actual_price: str                # 实付款
    buyer_info: str                  # 购买者信息 (手机号+指纹链接)
    status: str                      # 状态 (已支付/未支付等)
    card_status: str                 # 取卡状态 (已取/未取/已取部分)
    card_password: str = ""          # 取卡密码 (可能为空)
    trade_time: str                  # 交易时间 (如 2026-04-15 13:32:52)
    order_id: str = ""               # 订单ID (用于fetch链接)


class OrderQueryResponse(BaseModel):
    """订单查询响应"""
    success: bool
    message: str
    orders: list[OrderItem] = []
    total: int = 0
