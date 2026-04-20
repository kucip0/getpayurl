from app.services.xinfaka_service import XinfakaService


class QukapuService(XinfakaService):
    """趣卡铺服务（复用新发卡所有接口）"""

    PLATFORM_CODE = "qukapu"
    BASE_URL = "https://www.qukapu.com"
    TRACKING_COOKIE = "XSRF-TOKEN"
    FINGERPRINT_ENABLED = False

    def __init__(self, user_id: int, db):
        super().__init__(user_id, db)
        # 验证码相关属性（继承自XinfakaService但需要重新初始化）
        self.captcha_csrf_token = ""
        self.captcha_cookies = {}
    
    def log(self, message: str):
        """重写日志方法，同时输出到控制台和logs列表"""
        # 调用父类的log方法但使用不同的前缀
        from app.services.base_service import BaseService
        BaseService.log(self, message)
        print(f"\033[36m[Qukapu调试]\033[0m {message}", flush=True)
