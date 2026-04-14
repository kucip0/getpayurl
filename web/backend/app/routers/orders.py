from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, OrderLog
from app.schemas import PriceRequest, PriceResponse, OrderRequest, OrderResponse, ModifyPriceRequest, ModifyPriceResponse
from app.routers.platforms import get_service

router = APIRouter(prefix="/api/platforms", tags=["订单"])


@router.post("/{platform_code}/price", response_model=PriceResponse)
def get_price(
    platform_code: str,
    request: PriceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取商品价格"""
    # 调试日志
    print(f"DEBUG get_price: current_user.id={current_user.id}, current_user.username={current_user.username}, platform_code={platform_code}")
    
    service = get_service(platform_code, current_user.id, db)
    loaded = service.load_cookies()
    print(f"DEBUG get_price: cookies loaded={loaded}")
    
    # 检查配置是否存在
    from app.models import PlatformConfig
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()
    print(f"DEBUG get_price: config found={config is not None}")

    result = service.get_product_price(request.product_url)
    return PriceResponse(**result)


@router.post("/{platform_code}/modify-price", response_model=ModifyPriceResponse)
def modify_price(
    platform_code: str,
    request: ModifyPriceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改商品价格"""
    service = get_service(platform_code, current_user.id, db)
    service.load_cookies()

    # 调试日志
    print(f"DEBUG modify_price: platform_code={platform_code}, service type={type(service).__name__}")
    print(f"DEBUG modify_price: has modify_goods_price={hasattr(service, 'modify_goods_price')}")

    # 检查服务是否有改价方法
    if not hasattr(service, 'modify_goods_price'):
        raise HTTPException(status_code=400, detail=f"平台 {platform_code} 不支持改价功能")

    result = service.modify_goods_price(request.goods_id, request.new_price)
    return ModifyPriceResponse(**result)


@router.post("/{platform_code}/order", response_model=OrderResponse)
def submit_order(
    platform_code: str,
    request: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交订单并生成二维码"""
    service = get_service(platform_code, current_user.id, db)
    service.load_cookies()

    result = service.submit_order(request.product_url, request.new_price)

    # 记录订单日志
    order_log = OrderLog(
        user_id=current_user.id,
        platform_code=platform_code,
        product_url=request.product_url,
        new_price=request.new_price,
        status="success" if result["success"] else "failed",
        error_message=result.get("error_message"),
        qr_code_url=result.get("payment_url"),
    )
    db.add(order_log)
    db.commit()

    return OrderResponse(**result)
