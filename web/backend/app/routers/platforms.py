from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, PlatformConfig
from app.schemas import (
    PlatformInfo, PlatformListResponse,
    ShopLoginRequest, ShopLoginResponse
)

# 余额查询响应
from typing import Optional
from pydantic import BaseModel
import time
from typing import Dict

class BalanceResponse(BaseModel):
    success: bool
    message: str
    withdrawable: str = "0.000"
    non_withdrawable: str = "0.000"
from app.services.houfaka_service import HoufakaService
from app.services.siyun_service import SiyunService
from app.services.mengyan_service import MengyanService
from app.services.xinfaka_service import XinfakaService
from app.services.qukapu_service import QukapuService

router = APIRouter(prefix="/api/platforms", tags=["平台"])

# 缓存service实例（用于保持session）
_service_cache: Dict[str, dict] = {}
CACHE_EXPIRE = 300  # 5分钟过期


def get_cached_service(platform_code: str, user_id: int, db: Session) -> object:
    """获取或创建缓存的service实例（仅用于新发卡登录流程）"""
    cache_key = f"{user_id}_{platform_code}"
    
    # 检查缓存是否有效
    if cache_key in _service_cache:
        cache_data = _service_cache[cache_key]
        if time.time() - cache_data['time'] < CACHE_EXPIRE:
            return cache_data['service']
        else:
            # 过期，删除
            del _service_cache[cache_key]
    
    # 创建新实例并缓存
    service = get_service(platform_code, user_id, db)
    _service_cache[cache_key] = {
        'service': service,
        'time': time.time()
    }
    return service

PLATFORMS = [
    PlatformInfo(code="houfaka", name="猴发卡", host="https://www.houfaka.com"),
    PlatformInfo(code="siyun", name="四云发卡", host="https://shop.4yuns.com"),
    PlatformInfo(code="mengyan", name="梦言云卡", host="https://www.np4.cn"),
    PlatformInfo(code="xinfaka", name="新发卡", host="https://www.xinfaka.com"),
    PlatformInfo(code="qukapu", name="趣卡铺", host="https://www.qukapu.com"),
]


def get_service(platform_code: str, user_id: int, db: Session):
    """获取平台服务实例"""
    if platform_code == "houfaka":
        return HoufakaService(user_id, db)
    elif platform_code == "siyun":
        return SiyunService(user_id, db)
    elif platform_code == "mengyan":
        return MengyanService(user_id, db)
    elif platform_code == "xinfaka":
        return XinfakaService(user_id, db)
    elif platform_code == "qukapu":
        return QukapuService(user_id, db)
    else:
        raise HTTPException(status_code=404, detail="平台不存在")


@router.get("", response_model=PlatformListResponse)
def list_platforms(current_user: User = Depends(get_current_user)):
    """获取平台列表"""
    return PlatformListResponse(platforms=PLATFORMS)


@router.post("/{platform_code}/login", response_model=ShopLoginResponse)
def shop_login(
    platform_code: str,
    login_data: ShopLoginRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """店铺登录"""
    # 使用缓存的service实例（保持session）
    service = get_cached_service(platform_code, current_user.id, db)

    # 保存配置
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()

    if not config:
        config = PlatformConfig(
            user_id=current_user.id,
            platform_code=platform_code,
            shop_username=login_data.username,
            shop_password=login_data.password,
        )
        db.add(config)
    else:
        config.shop_username = login_data.username
        config.shop_password = login_data.password

    db.commit()

    try:
        # 获取验证码参数和 CSRF Token
        verify_code = getattr(login_data, 'verify_code', '')
        csrf_token = getattr(login_data, 'csrf_token', '')
        
        # 调用登录方法（使用缓存的session）
        result = service.login(login_data.username, login_data.password, verify_code, csrf_token)
        service.save_cookies()
        return ShopLoginResponse(
            success=True,
            message=result["message"],
            shop_name=result.get("shop_name"),
        )
    except Exception as e:
        return ShopLoginResponse(
            success=False,
            message=str(e)
        )


@router.get("/{platform_code}/balance", response_model=BalanceResponse)
def get_balance(
    platform_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询店铺账户余额"""
    service = get_service(platform_code, current_user.id, db)
    
    # 检查服务是否有余额查询方法
    if not hasattr(service, 'get_balance'):
        raise HTTPException(status_code=400, detail=f"平台 {platform_code} 不支持余额查询功能")
    
    result = service.get_balance()
    
    return BalanceResponse(**result)


@router.get("/{platform_code}/captcha")
def get_captcha(
    platform_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取验证码图片和CSRF Token（仅新发卡平台需要）"""
    from fastapi.responses import JSONResponse
    
    # 使用缓存的service实例（保持session）
    service = get_cached_service(platform_code, current_user.id, db)
    
    # 检查服务是否有获取验证码方法
    if not hasattr(service, 'get_captcha_image'):
        raise HTTPException(status_code=400, detail=f"平台 {platform_code} 不需要验证码")
    
    try:
        # 获取验证码图片
        captcha_data = service.get_captcha_image()
        
        # 返回图片和 CSRF Token
        return JSONResponse(content={
            "success": True,
            "captcha_base64": captcha_data.hex(),  # 转换为hex传输
            "csrf_token": getattr(service, 'captcha_csrf_token', '')
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
