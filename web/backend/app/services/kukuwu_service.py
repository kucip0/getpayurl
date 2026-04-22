from app.services.xinfaka_service import XinfakaService


class KukuwuService(XinfakaService):
    """酷卡屋服务（复用趣卡铺所有接口）"""

    PLATFORM_CODE = "kukuwu"
    BASE_URL = "https://kkw.yiyipay.com"
    TRACKING_COOKIE = "XSRF-TOKEN"
    FINGERPRINT_ENABLED = False

    def __init__(self, user_id: int, db):
        super().__init__(user_id, db)
        # 验证码相关属性（继承自XinfakaService但需要重新初始化）
        self.captcha_csrf_token = ""
        self.captcha_cookies = {}
        self.captcha_cookies_loaded = False
    
    def log(self, message: str):
        """重写日志方法，同时输出到控制台和logs列表"""
        # 调用父类的log方法但使用不同的前缀
        from app.services.base_service import BaseService
        BaseService.log(self, message)
        print(f"\033[36m[Kukuwu调试]\033[0m {message}", flush=True)
    
    def _mobile_step2_create_order(self, product_url: str, goods_info: dict, csrf_token: str, new_price: float, pay_id: str) -> str:
        """步骤2: 创建订单 POST /goods/createorder（使用动态获取的payId）"""
        
        # 构建订单数据 - 使用动态获取的payId
        order_data = {
            "GoodsId": goods_info["goods_id"],
            "quantity": "1",
            "shopId": goods_info["shop_id"],
            "is_sms": "0",
            "sms_receive": "",
            "take_card_password": "",
            "payId": pay_id,  # 动态获取的支付渠道ID
            "payType": "1",
            "coupon": "",
            "is_xh": "0",
            "kami_id": "",
            "is_dk": "0",
            "visit_password": "",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRF-TOKEN": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": self.BASE_URL,
            "Referer": product_url,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        }

        resp = self.session.post(
            f"{self.BASE_URL}/goods/createorder",
            data=order_data,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()

        # 解析响应
        try:
            result = resp.json()
            if result.get("code") != 0:
                error_msg = result.get("msg", "创建订单失败")
                raise Exception(f"创建订单失败: {error_msg}")
            
            # 提取订单号 - 从 data.url 中
            data = result.get("data", {})
            
            # data 可能是列表或字典
            url = ""
            if isinstance(data, list) and data:
                url = data[0].get("url", "")
            elif isinstance(data, dict):
                url = data.get("url", "")
            
            if url:
                # URL格式: https://kkw.yiyipay.com/paymentconfirm/KKW...
                order_no = url.split("/")[-1]
                return order_no
            
            # 备用方案: 直接从响应中提取
            order_no = result.get("order_id") or result.get("trade_no")
            if order_no:
                return order_no
            
            raise Exception(f"响应中未找到订单号: {result}")
        except Exception as e:
            # 如果响应不是JSON，尝试从HTML中提取
            import re
            if "trade_no" in resp.text:
                match = re.search(r'name="trade_no"\s+value="([^"]+)"', resp.text)
                if match:
                    return match.group(1)
            raise
