import json
import uuid
from typing import Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from app.models import PlatformConfig
from app.utils.http_client import create_session
from app.utils.qr_generator import generate_qr_base64


class BaseService:
    """基础服务类"""
    
    PLATFORM_CODE: str = ""
    BASE_URL: str = ""
    TRACKING_COOKIE: str = ""
    FINGERPRINT_ENABLED: bool = False
    
    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.session = create_session(verify_ssl=False)
        self.fingerprint = str(uuid.uuid4())
        self.logs: List[str] = []
    
    def log(self, message: str):
        """添加日志（过滤BOM字符，避免Windows终端编码错误）"""
        # 移除BOM字符和其他可能导致编码问题的字符
        clean_message = message.replace('\ufeff', '').encode('gbk', 'ignore').decode('gbk')
        self.logs.append(clean_message)
    
    def load_cookies(self) -> bool:
        """从数据库加载Cookie"""
        config = self.db.query(PlatformConfig).filter(
            PlatformConfig.user_id == self.user_id,
            PlatformConfig.platform_code == self.PLATFORM_CODE
        ).first()
        
        if not config or not config.cookies:
            return False
        
        try:
            cookies = json.loads(config.cookies)
            for cookie in cookies:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain"),
                )
            return True
        except (json.JSONDecodeError, KeyError):
            return False
    
    def save_cookies(self):
        """保存Cookie到数据库"""
        config = self.db.query(PlatformConfig).filter(
            PlatformConfig.user_id == self.user_id,
            PlatformConfig.platform_code == self.PLATFORM_CODE
        ).first()
        
        if not config:
            return
        
        cookies_list = []
        for cookie in self.session.cookies:
            cookies_list.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
            })
        
        config.cookies = json.dumps(cookies_list)
        self.db.commit()
    
    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格（子类实现）"""
        raise NotImplementedError
    
    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单（子类实现）"""
        raise NotImplementedError
