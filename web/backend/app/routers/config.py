from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, PlatformConfig
from app.schemas import PlatformConfigResponse, PlatformConfigUpdate
from app.routers.platforms import get_cached_service

router = APIRouter(prefix="/api/config", tags=["配置"])


@router.get("/{platform_code}", response_model=PlatformConfigResponse)
def get_config(
    platform_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取平台配置，并通过查询余额验证登录状态"""
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()

    if not config:
        return PlatformConfigResponse()

    product_urls = []
    if config.product_urls:
        try:
            product_urls = json.loads(config.product_urls)
        except json.JSONDecodeError:
            product_urls = []

    # 通过查询余额验证登录状态（只有余额查询成功才视为已登录）
    has_login = False
    if config.shop_username and config.shop_password and config.cookies:
        try:
            service = get_cached_service(platform_code, current_user.id, db)
            if hasattr(service, 'get_balance'):
                result = service.get_balance()
                has_login = result.get("success", False)
        except Exception:
            has_login = False

    return PlatformConfigResponse(
        shop_username=config.shop_username,
        product_urls=product_urls,
        has_login=has_login,
    )


@router.put("/{platform_code}")
def update_config(
    platform_code: str,
    update_data: PlatformConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新平台配置"""
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()

    if not config:
        config = PlatformConfig(
            user_id=current_user.id,
            platform_code=platform_code,
        )
        db.add(config)

    if update_data.shop_username is not None:
        config.shop_username = update_data.shop_username

    config.product_urls = json.dumps(update_data.product_urls)
    db.commit()

    return {"message": "配置保存成功"}
