import json
import random
import re
from typing import Tuple, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.html_parser import unescape_html


class XinfakaService(BaseService):
    """新发卡服务"""

    PLATFORM_CODE = "xinfaka"
    BASE_URL = "https://www.xinfaka.com"
    TRACKING_COOKIE = "XSRF-TOKEN"
    FINGERPRINT_ENABLED = False

    def __init__(self, user_id: int, db):
        super().__init__(user_id, db)
        self.captcha_csrf_token = ""  # 保存 CSRF Token
        self.captcha_cookies = {}  # 保存验证码请求的cookies
    
    def log(self, message: str):
        """重写日志方法，同时输出到控制台和logs列表"""
        super().log(message)
        print(f"\033[33m[Xinfaka调试]\033[0m {message}", flush=True)
    
    def set_captcha_session(self, csrf_token: str, cookies: dict):
        """设置验证码请求的session（前端获取验证码后调用）"""
        self.captcha_csrf_token = csrf_token
        self.captcha_cookies = cookies
        self.log(f"设置验证码Session: CSRF Token={csrf_token[:30]}..., Cookies={list(cookies.keys())}")
    
    def load_captcha_session(self):
        """从数据库加载验证码session cookies"""
        self.log(f"尝试加载验证码Session, captcha_cookies={self.captcha_cookies}")
        if self.captcha_cookies:
            # 清除所有现有cookies
            self.session.cookies.clear()
            # 使用字典方式设置cookies（避免重复cookie问题）
            from requests.cookies import create_cookie
            for key, value in self.captcha_cookies.items():
                # 直接设置cookie，不指定domain和path（让requests自动处理）
                cookie = create_cookie(key, value)
                self.session.cookies.set_cookie(cookie)
            self.log(f"已加载验证码Session Cookies: {list(self.captcha_cookies.keys())}")
            self.log(f"当前Session所有Cookies: {dict(self.session.cookies)}")
            self.log(f"CSRF Token: {self.captcha_csrf_token[:30] if self.captcha_csrf_token else '未设置'}...")

    def login(self, username: str, password: str, verify_code: str = "", csrf_token: str = "") -> dict:
        """登录新发卡平台（使用缓存的session）"""
        try:
            if not verify_code:
                raise Exception("请输入验证码")
            if not csrf_token:
                raise Exception("缺少CSRF Token")
            
            self.log(f"CSRF Token: {csrf_token[:50]}...")
            self.log(f"当前Cookies: {dict(self.session.cookies)}")

            login_data = {
                "mobile": username,
                "password": password,
                "verify_code": verify_code,
                "keeplogin": "0",
                "_token": csrf_token,
            }

            self.log("=" * 80)
            self.log("【登录请求】")
            self.log(f"  URL: {self.BASE_URL}/hp2025/merchant/login")
            self.log(f"  请求体: mobile={username}, verify_code={verify_code}")
            self.log(f"  Cookies: {dict(self.session.cookies)}")
            self.log("=" * 80)

            resp = self.session.post(
                f"{self.BASE_URL}/hp2025/merchant/login",
                data=login_data,
                timeout=15
            )
            
            self.log("=" * 80)
            self.log("【登录响应】")
            self.log(f"  状态码: {resp.status_code}")
            self.log(f"  返回Cookies: {dict(resp.cookies)}")
            self.log(f"  响应: {resp.text[:200]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            self.log(f"登录响应JSON: {json.dumps(result, ensure_ascii=False)}")

            if result.get("code") != 0:
                error_msg = result.get("msg", "登录失败")
                data = result.get("data", {})
                if isinstance(data, dict) and data.get("type") in [1, 2]:
                    login_type = data["type"]
                    type_name = "SMS" if login_type == 1 else "Email"
                    value = data.get("value", "")
                    raise Exception(f"需要{type_name}二级验证,验证账号: {value}")
                raise Exception(f"登录失败: {error_msg}")

            xsh_cookie = self.session.cookies.get("xsh_session")
            if not xsh_cookie and not dict(self.session.cookies):
                raise Exception("登录失败: 服务器未返回Cookie")
            
            self.log("登录成功")
            return {
                "success": True,
                "message": "登录成功",
                "shop_name": username,
            }

        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise
            
            # ===== 输出登录响应详情 =====
            self.log("=" * 80)
            self.log("【登录响应】详情:")
            self.log(f"  状态码: {resp.status_code}")
            self.log(f"  响应头: {dict(resp.headers)}")
            self.log(f"  返回Cookies: {dict(resp.cookies)}")
            self.log(f"  响应后Session所有Cookies: {dict(self.session.cookies)}")
            self.log(f"  响应内容: {resp.text[:300]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            self.log(f"登录响应JSON: {json.dumps(result, ensure_ascii=False)}")

            # 5. 检查响应
            if result.get("code") != 0:
                error_msg = result.get("msg", "登录失败")
                
                # 检查是否需要二级验证
                data = result.get("data", {})
                if isinstance(data, dict) and data.get("type") in [1, 2]:
                    login_type = data["type"]
                    type_name = "SMS" if login_type == 1 else "Email"
                    value = data.get("value", "")
                    raise Exception(f"需要{type_name}二级验证,验证账号: {value}")
                
                raise Exception(f"登录失败: {error_msg}")

            # 6. 验证 Cookie (xsh_session 或 remember_merchant_*)
            xsh_cookie = self.session.cookies.get("xsh_session")
            if not xsh_cookie:
                all_cookies = dict(self.session.cookies)
                if not all_cookies:
                    raise Exception("登录失败: 服务器未返回 Cookie")
                self.log("登录成功(Cookie 检查通过)")
            else:
                self.log("登录成功")

            return {
                "success": True,
                "message": "登录成功",
                "shop_name": username,
            }

        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise

    def get_captcha_image(self) -> bytes:
        """获取验证码图片(同时获得CSRF Token)"""
        try:
            # 清除旧的 session,确保获取新的 CSRF Token
            self.session.cookies.clear()
            self.captcha_csrf_token = ""
            
            # 获取验证码图片(响应会设置 XSRF-TOKEN Cookie)
            import random
            captcha_url = f"{self.BASE_URL}/captcha/default?{random.random()}"
            
            # ===== 输出请求详情 =====
            self.log("=" * 80)
            self.log("【获取验证码】请求详情:")
            self.log(f"  请求URL: {captcha_url}")
            self.log(f"  请求方法: GET")
            self.log(f"  请求头: {dict(self.session.headers)}")
            self.log(f"  当前Cookies: {dict(self.session.cookies)}")
            self.log("=" * 80)
            
            resp = self.session.get(captcha_url, timeout=15)
            resp.raise_for_status()
            
            # ===== 输出响应详情 =====
            self.log("【获取验证码】响应详情:")
            self.log(f"  状态码: {resp.status_code}")
            self.log(f"  响应头: {dict(resp.headers)}")
            self.log(f"  返回Cookies: {dict(resp.cookies)}")
            self.log(f"  响应后Session所有Cookies: {dict(self.session.cookies)}")
            self.log(f"  响应内容大小: {len(resp.content)} bytes")
            
            # 从 Cookie 中获取 CSRF Token (XSRF-TOKEN)
            csrf_token = self.session.cookies.get("XSRF-TOKEN")
            if csrf_token:
                from urllib.parse import unquote
                # URL解码
                csrf_token = unquote(csrf_token)
                self.captcha_csrf_token = csrf_token
                self.log(f"  CSRF Token (解码后): {csrf_token[:50]}...")
                self.log(f"  CSRF Token 长度: {len(csrf_token)}")
            else:
                self.log("  警告: 未获取到 CSRF Token")
            
            self.log("=" * 80)
            return resp.content
        except Exception as e:
            self.log(f"获取验证码失败: {str(e)}")
            raise

    def login_with_captcha_session(self, username: str, password: str, verify_code: str) -> dict:
        """使用已获取验证码的 session 登录(保持 session 一致性)
        
        这个方法必须在 get_captcha_image() 之后调用,使用同一个 session
        """
        # 直接使用已保存的 CSRF Token 和 session
        if not self.captcha_csrf_token:
            raise Exception("请先获取验证码")
        
        try:
            # POST 登录(使用同一个 session)
            login_data = {
                "mobile": username,
                "password": password,
                "verify_code": verify_code,
                "keeplogin": "0",
                "_token": self.captcha_csrf_token,
            }

            # 使用 multipart/form-data (根据抓包)
            resp = self.session.post(
                f"{self.BASE_URL}/hp2025/merchant/login",
                data=login_data,
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()

            self.log(f"登录响应: {result}")

            # 检查响应
            if result.get("code") != 0:
                error_msg = result.get("msg", "登录失败")
                
                data = result.get("data", {})
                if isinstance(data, dict) and data.get("type") in [1, 2]:
                    login_type = data["type"]
                    type_name = "SMS" if login_type == 1 else "Email"
                    value = data.get("value", "")
                    raise Exception(f"需要{type_name}二级验证,验证账号: {value}")
                
                raise Exception(f"登录失败: {error_msg}")

            # 验证 Cookie
            xsh_cookie = self.session.cookies.get("xsh_session")
            if not xsh_cookie:
                all_cookies = dict(self.session.cookies)
                if not all_cookies:
                    raise Exception("登录失败: 无 Cookie")
                self.log("登录成功(Cookie 检查通过)")
            else:
                self.log("登录成功")

            return {
                "success": True,
                "message": "登录成功",
                "shop_name": username,
            }

        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise

    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格和信息(使用/goods/getinfo API)"""
        try:
            # 步骤1: 访问商品页面获取shopId和CSRF Token
            resp = self.session.get(product_url, timeout=15)
            resp.raise_for_status()
            
            html = resp.text
            
            # 提取 CSRF Token
            csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
            csrf_token = csrf_match.group(1) if csrf_match else ""
            
            # 提取 shopId (从隐藏input)
            soup = BeautifulSoup(html, "html.parser")
            shop_id_input = soup.find("input", {"id": "shopId"})
            if not shop_id_input:
                raise Exception("未找到 shopId")
            shop_id = shop_id_input.get("value")
            
            # 提取商品ID (从URL或页面)
            # URL格式: https://www.xinfaka.com/single/8BF70AA3E39D
            # 但实际API使用的是数字ID,需要从页面获取
            goods_id_input = soup.find("input", {"id": "GoodsId"})
            if not goods_id_input:
                raise Exception("未找到商品ID")
            goods_id = goods_id_input.get("value")
            
            self.log(f"商品信息: shopId={shop_id[:20]}..., goodsId={goods_id}")
            
            # 步骤2: 调用 /goods/getinfo API
            api_url = f"{self.BASE_URL}/goods/getinfo"
            data = {
                "shopId": shop_id,
                "id": goods_id
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": self.BASE_URL,
                "Referer": product_url,
            }
            
            resp = self.session.post(api_url, data=data, headers=headers, timeout=15)
            resp.raise_for_status()
            
            result = resp.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")
            
            goods_data = result.get("data", {})
            
            # 提取商品信息
            product_name = goods_data.get("name", "未知商品")
            price = goods_data.get("price", "0.00")
            stock = goods_data.get("stock", 0)
            sms_price = goods_data.get("smsPrice", "0.00")
            
            self.log(f"获取商品信息成功: {product_name}, 价格: ¥{price}, 库存: {stock}")
            
            return {
                "success": True,
                "product_id": goods_id,
                "product_name": product_name,
                "original_price": float(price),
                "stock": stock,
                "sms_price": float(sms_price),
            }
            
        except Exception as e:
            self.log(f"获取商品价格失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def modify_goods_price(self, goods_id: str, new_price: str) -> dict:
        """修改商品价格（使用直接修改API）"""
        try:
            self.log(f"正在修改商品 {goods_id} 价格为 ¥{new_price}...")
            
            # 调用直接修改价格API
            result = self._direct_modify_price(goods_id, new_price)
            
            self.log(f"成功: 价格已修改为 ¥{new_price}")
            return {
                "success": True,
                "message": f"价格已修改为 ¥{new_price}",
                "goods_id": goods_id,
                "new_price": new_price,
            }
            
        except Exception as e:
            self.log(f"修改价格失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _direct_modify_price(self, goods_id: str, new_price: str) -> dict:
        """直接修改商品价格（使用 /merchant/goods/modify API）"""
        modify_url = f"{self.BASE_URL}/merchant/goods/modify"
        
        # 获取 CSRF Token - 先访问商户首页确认登录状态
        self.log("正在获取CSRF Token并检查登录状态...")
        resp = self.session.get(f"{self.BASE_URL}/merchant", timeout=15)
        
        if resp.status_code == 500:
            raise Exception("服务器错误，可能未登录或session已过期")
        
        resp.raise_for_status()
        
        # 从页面中提取 CSRF Token
        csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', resp.text)
        if not csrf_match:
            # 检查是否跳转到登录页
            if 'login' in resp.url.lower() or '登录' in resp.text:
                raise Exception("未登录或登录已过期，请重新登录")
            raise Exception("无法获取CSRF Token")
        
        csrf_token = csrf_match.group(1)
        self.log(f"获取到CSRF Token: {csrf_token[:30]}...")
        
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": csrf_token,
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/merchant/goods/list",
            "sec-ch-ua": '"Google Chrome";v="147", "Not-A.Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        
        # 只需传递三个参数：id, value, field
        form_data = {
            "id": str(goods_id),
            "value": str(new_price),
            "field": "price"
        }
        
        self.log(f"提交价格修改: goods_id={goods_id}, new_price={new_price}")
        
        resp = self.session.post(
            modify_url,
            data=form_data,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        # 解析响应
        result = resp.json()
        self.log(f"价格修改响应: {result}")
        
        # 抓包返回 code=0 表示成功
        if result.get("code") != 0:
            error_msg = result.get("msg", "修改商品价格失败，未知错误")
            raise Exception(f"修改商品价格失败: {error_msg}")
        
        return result


    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单并获取支付二维码（基于移动端接口）"""
        self.logs = []

        try:
            # 清除旧Cookie
            self.session.cookies.clear()
            self.log("步骤1前: 已清除旧Cookie")

            # 步骤1: 获取商品页面和 CSRF Token
            csrf_token, goods_info = self._mobile_step1_get_goods_page(product_url, new_price)

            # 步骤1.5: 动态获取支付渠道ID（支付宝 channel_type=2）
            pay_id = self._get_pay_channel_id(goods_info, csrf_token)
            self.log(f"获取到支付渠道ID: {pay_id}")

            # 步骤2: 创建订单
            order_no = self._mobile_step2_create_order(product_url, goods_info, csrf_token, new_price, pay_id)
            self.log(f"订单创建成功: {order_no}")

            # 步骤3: 访问支付页面 /payment/{订单号} 获取支付宝支付链接
            payment_url = self._mobile_step3_get_payment_url(order_no, csrf_token)

            # 步骤4: 生成二维码
            qr_base64 = self._generate_qrcode(payment_url)

            return {
                "success": True,
                "order_id": order_no,
                "qr_code_base64": qr_base64,
                "payment_url": payment_url,
                "logs": self.logs,
            }

        except Exception as e:
            self.log(f"订单处理失败: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "logs": self.logs,
            }

    def _mobile_step1_get_goods_page(self, url: str, new_price: float) -> Tuple[str, dict]:
        """步骤1: 获取商品页面，提取 CSRF Token 和商品信息"""
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()

        html = resp.text
        
        # 提取 CSRF Token
        csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
        if not csrf_match:
            raise Exception("未找到 CSRF Token")
        csrf_token = csrf_match.group(1)
        self.log(f"获取 CSRF Token: {csrf_token[:20]}...")

        soup = BeautifulSoup(html, "html.parser")

        # 提取商品ID (从隐藏input)
        goods_id_input = soup.find("input", {"id": "GoodsId"})
        if not goods_id_input:
            raise Exception("未找到商品ID")
        goods_id = goods_id_input.get("value")

        # 提取 shopId
        shop_id_input = soup.find("input", {"id": "shopId"})
        if not shop_id_input:
            raise Exception("未找到 shopId")
        shop_id = shop_id_input.get("value")

        # 提取商品价格
        price_input = soup.find("input", {"id": "goodsPrice"})
        original_price = price_input.get("value", "0") if price_input else "0"

        self.log(f"商品信息: ID={goods_id}, 价格={original_price}, shopId={shop_id[:20]}...")

        return csrf_token, {
            "goods_id": goods_id,
            "shop_id": shop_id,
            "original_price": original_price,
        }

    def _get_pay_channel_id(self, goods_info: dict, csrf_token: str) -> str:
        """动态获取支付渠道ID（支付宝 - 通过image字段检测）
        
        请求 POST /goods/getrate 获取支付渠道列表，提取image包含"zfb"的渠道ID
        """
        url = f"{self.BASE_URL}/goods/getrate"
        
        data = {
            "userid": goods_info["shop_id"],
            "goods_id": goods_info["goods_id"],
            "isMobile": "1"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRF-TOKEN": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        }
        
        # 打印详细调试日志
        self.log("=" * 80)
        self.log("【调试】获取支付渠道 - 请求信息")
        self.log(f"请求URL: {url}")
        self.log(f"请求方法: POST")
        self.log(f"请求头:")
        for k, v in headers.items():
            self.log(f"  {k}: {v}")
        self.log(f"请求体 (urlencode后):")
        from urllib.parse import urlencode
        encoded_data = urlencode(data)
        self.log(f"  {encoded_data}")
        self.log("=" * 80)
        
        resp = self.session.post(url, data=data, headers=headers, timeout=15)
        
        # 打印响应信息
        self.log("=" * 80)
        self.log("【调试】获取支付渠道 - 响应信息")
        self.log(f"响应状态码: {resp.status_code}")
        self.log(f"响应头:")
        for k, v in resp.headers.items():
            # 只打印前100个字符，避免Cookie太长
            v_display = v[:100] + "..." if len(v) > 100 else v
            self.log(f"  {k}: {v_display}")
        self.log(f"响应体长度: {len(resp.text)} 字符")
        self.log(f"响应体内容 (前2000字符):")
        self.log(resp.text[:2000])
        self.log("=" * 80)
        
        resp.raise_for_status()
        
        # 解析JSON响应
        result = resp.json()
        self.log(f"【调试】JSON解析结果: {result}")
        
        if not result.get("success") or not result.get("data"):
            self.log(f"警告: 响应中没有渠道数据，使用默认payId=13")
            return "13"
        
        # 遍历渠道列表，查找image包含"zfb"的渠道（支付宝）
        channels = result["data"]
        alipay_channel_id = None
        
        for channel in channels:
            channel_id = channel.get("channel_id")
            image = channel.get("image", "")
            self.log(f"【调试】检查渠道: channel_id={channel_id}, image={image}")
            
            if "zfb" in image:  # image路径包含"zfb"表示支付宝
                alipay_channel_id = str(channel_id)
                self.log(f"【调试】找到支付宝渠道: channel_id={alipay_channel_id}")
                break
        
        if alipay_channel_id:
            self.log(f"找到支付宝支付渠道ID: {alipay_channel_id}")
            return alipay_channel_id
        else:
            self.log(f"警告: 未找到支付宝渠道(image包含zfb)，使用第一个渠道")
            if channels:
                return str(channels[0].get("channel_id", "13"))
            return "13"

    def _mobile_step2_create_order(self, product_url: str, goods_info: dict, csrf_token: str, new_price: float, pay_id: str) -> str:
        """步骤2: 创建订单 POST /goods/createorder (使用动态获取的payId)"""
        
        # 构建订单数据 - 使用动态获取的payId
        order_data = {
            "GoodsId": goods_info["goods_id"],
            "quantity": "1",
            "shopId": goods_info["shop_id"],
            "is_sms": "0",
            "sms_receive": "",
            "take_card_password": "",
            "payId": pay_id,  # 动态获取的支付渠道ID
            "payType": "1",  # 支付宝
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
        
        # 打印详细调试日志
        url = f"{self.BASE_URL}/goods/createorder"
        self.log("=" * 80)
        self.log("【调试】创建订单 - 请求信息")
        self.log(f"请求URL: {url}")
        self.log(f"请求方法: POST")
        self.log(f"请求头:")
        for k, v in headers.items():
            self.log(f"  {k}: {v}")
        self.log(f"请求体 (urlencode后):")
        from urllib.parse import urlencode
        encoded_data = urlencode(order_data)
        self.log(f"  {encoded_data}")
        self.log("=" * 80)

        resp = self.session.post(url, data=order_data, headers=headers, timeout=15)
        
        # 打印响应信息
        self.log("=" * 80)
        self.log("【调试】创建订单 - 响应信息")
        self.log(f"响应状态码: {resp.status_code}")
        self.log(f"响应头:")
        for k, v in resp.headers.items():
            v_display = v[:100] + "..." if len(v) > 100 else v
            self.log(f"  {k}: {v_display}")
        self.log(f"响应体长度: {len(resp.text)} 字符")
        self.log(f"响应体内容:")
        self.log(resp.text[:2000])
        self.log("=" * 80)
        
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
                # URL格式: https://www.xinfaka.com/paymentconfirm/XFK...
                order_no = url.split("/")[-1]
                return order_no
            
            # 备用方案: 直接从响应中提取
            order_no = result.get("order_id") or result.get("trade_no")
            if order_no:
                return order_no
            
            raise Exception(f"响应中未找到订单号: {result}")
        except Exception as e:
            # 如果响应不是JSON，尝试从HTML中提取
            if "trade_no" in resp.text:
                match = re.search(r'name="trade_no"\s+value="([^"]+)"', resp.text)
                if match:
                    return match.group(1)
            raise

    def _mobile_step3_get_payment_url(self, order_no: str, csrf_token: str) -> str:
        """步骤3: 访问支付页面,跟随重定向获取支付宝支付链接
        
        流程:
        1. /payment/{订单号} -> 302
        2. /disburse/{订单号} -> 302
        3. www.yiyipay.com/payment/YY... -> 200 (包含支付宝表单)
        4. 提取表单参数并提交到支付宝网关
        5. 获取302重定向URL
        6. 跟随重定向获取最终支付链接
        
        Returns:
            str: 最终的支付宝支付URL
        """
        from collections import OrderedDict
        
        pay_url = f"{self.BASE_URL}/payment/{order_no}"
        
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "X-CSRF-TOKEN": csrf_token,
            "Referer": f"{self.BASE_URL}/",
        }

        # 第1次: /payment/{订单号} -> 302
        self.log(f"访问支付页: {pay_url}")
        resp1 = self.session.get(pay_url, headers=headers, timeout=15, allow_redirects=False)
        resp1.raise_for_status()
        
        if resp1.status_code not in [301, 302]:
            raise Exception(f"支付页未重定向, 状态码: {resp1.status_code}")
        
        url2 = resp1.headers.get("Location")
        if not url2:
            raise Exception("未找到第一次重定向URL")
        self.log(f"重定向1: {url2[:80]}...")
        
        # 第2次: /disburse/{订单号} -> 302
        resp2 = self.session.get(url2, headers=headers, timeout=15, allow_redirects=False)
        resp2.raise_for_status()
        
        if resp2.status_code not in [301, 302]:
            raise Exception(f"/disburse 未重定向, 状态码: {resp2.status_code}")
        
        url3 = resp2.headers.get("Location")
        if not url3:
            raise Exception("未找到第二次重定向URL")
        self.log(f"重定向2: {url3[:80]}...")
        
        # 第3次: www.yiyipay.com -> 200 (包含支付宝表单)
        # 根据抓包，Referer 应该是发卡平台首页
        headers3 = headers.copy()
        headers3["Referer"] = f"{self.BASE_URL}/"
        
        resp3 = self.session.get(url3, headers=headers3, timeout=15)
        resp3.raise_for_status()
        
        # 解析HTML,提取支付宝表单参数
        soup = BeautifulSoup(resp3.text, "html.parser")
        form = soup.find("form", {"id": "alipaysubmit"})
        
        if not form:
            raise Exception("未找到支付宝表单")
        
        # 提取所有隐藏字段
        alipay_params = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value")
            if name and value is not None:
                alipay_params[name] = value
        
        if not alipay_params:
            raise Exception("支付宝表单参数为空")
        
        self.log(f"提取到 {len(alipay_params)} 个支付宝表单参数")
        
        # 第4次: 提交到支付宝网关
        # 根据抓包分析,charset=utf8(不加横杠)
        gateway_url = "https://openapi.alipay.com/gateway.do?charset=utf8"
        
        # 直接提交原始表单参数
        encoded_data = urlencode(alipay_params)
        
        self.log(f"请求数据长度: {len(encoded_data)}")
        
        # 提交到支付宝网关(使用抓包的请求头)
        submit_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": "https://www.yiyipay.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://www.yiyipay.com/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        resp4 = self.session.post(
            gateway_url,
            data=encoded_data,
            headers=submit_headers,
            timeout=15,
            allow_redirects=False
        )
        
        self.log(f"支付宝网关响应: {resp4.status_code}")
        
        # 处理302重定向
        if resp4.status_code in [301, 302]:
            location = resp4.headers.get("Location")
            if not location:
                raise Exception("支付宝网关响应中无Location字段")
            
            self.log(f"支付宝网关重定向: {location[:100]}...")
            
            # 合并Cookie
            alipay_cookies = dict(resp4.cookies)
            all_cookies = {}
            for k, v in self.session.cookies.items():
                all_cookies[k] = v
            for k, v in alipay_cookies.items():
                all_cookies[k] = v
            
            # 第1次重定向: /cashier/mobilepay.htm
            resp5 = self.session.get(
                location,
                cookies=all_cookies,
                allow_redirects=False,
                timeout=15
            )
            
            self.log(f"第1次重定向响应: {resp5.status_code}")
            
            if resp5.status_code in [301, 302]:
                # 第2次重定向: /h5pay/landing/index.html
                final_url = resp5.headers.get("Location")
                if final_url:
                    self.log(f"第2次重定向: {final_url[:100]}...")
                    return final_url
                else:
                    raise Exception("未找到第2次重定向URL")
            else:
                # 如果没有第2次重定向,使用第1次的URL
                self.log(f"使用第1次重定向URL: {resp5.url[:100]}...")
                return resp5.url
            
        else:
            raise Exception(f"支付宝网关返回异常状态码: {resp4.status_code}, 响应: {resp4.text[:200]}")

    def _generate_qrcode(self, url: str) -> str:
        """生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("生成二维码成功")
        return qr_base64

    def _step1_get_cookie_and_params(self, url: str) -> Tuple[str, dict]:
        """步骤1: 获取Cookie及商品参数"""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path

        self.session.cookies.clear()
        self.log(f"DEBUG1-STEP1: 请求商品页面之前，已清除所有Cookie")

        request_url = f"{base_url}{path}"
        self.log(f"DEBUG1-STEP1: 请求URL={request_url}")
        
        step1_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Upgrade-Insecure-Requests": "1",
        }
        
        resp = self.session.get(request_url, headers=step1_headers, timeout=15)
        
        self.log(f"DEBUG1-STEP1: 响应状态码={resp.status_code}")
        self.log(f"DEBUG1-STEP1: response cookies={dict(resp.cookies)}")
        
        if resp.status_code != 200:
            raise Exception(f"步骤1请求失败: HTTP {resp.status_code}")

        # 处理转义的HTML
        html = resp.text.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')

        # 提取 CSRF Token
        csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else ""

        # 解析 HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # 提取隐藏字段
        def get_input_value(name):
            inp = soup.find("input", {"name": name})
            return inp.get("value", "") if inp else ""

        goodid = get_input_value("goodid")
        userid = get_input_value("userid")
        token = get_input_value("token")
        cateid = get_input_value("cateid")
        price = get_input_value("price")
        danjia = get_input_value("danjia")
        kucun = get_input_value("kucun")
        feePayer = get_input_value("feePayer")
        fee_rate = get_input_value("fee_rate")
        min_fee = get_input_value("min_fee")
        rate = get_input_value("rate")

        if not all([goodid, userid, token]):
            raise Exception("步骤1: 商品页面解析失败，缺少必要参数 (goodid/userid/token)")

        params = {
            "goodid": goodid,
            "userid": userid,
            "token": token,
            "cateid": cateid,
            "price": price,
            "danjia": danjia,
            "kucun": kucun,
            "feePayer": feePayer if feePayer else "2",
            "fee_rate": fee_rate if fee_rate else "0.05",
            "min_fee": min_fee if min_fee else "0.1",
            "rate": rate if rate else "100",
            "is_contact_limit": "default",
            "limit_quantity": "1",
            "cardNoLength": "0",
            "cardPwdLength": "0",
            "is_discount": "0",
            "coupon_ctype": "0",
            "coupon_value": "0",
            "sms_price": "0",
            "is_pwdforsearch": "",
            "is_coupon": "",
            "select_cards": "",
        }

        self.log("步骤1: 获取Cookie和商品参数成功")
        return csrf_token, params

    def _step2_submit_order(self, cookie: str, params: dict, product_url: str) -> str:
        """步骤2: 提交订单"""
        from urllib.parse import urlparse

        contact = f"1{random.randint(3,9)}{''.join([str(random.randint(0,9)) for _ in range(9)])}"

        quantity = 1
        price_val = float(params["price"]) if params["price"] else float(params["danjia"])
        fee_rate_val = float(params["fee_rate"])
        paymoney = round(price_val * quantity * (1 + fee_rate_val), 2)

        parsed = urlparse(product_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        order_data = {
            "goodid": params["goodid"],
            "cateid": params["cateid"],
            "quantity": str(quantity),
            "contact": contact,
            "email": "",
            "couponcode": "",
            "pwdforsearch1": "",
            "pwdforsearch2": "",
            "is_contact_limit": params["is_contact_limit"],
            "limit_quantity": params["limit_quantity"],
            "userid": params["userid"],
            "token": params["token"],
            "cardNoLength": params["cardNoLength"],
            "cardPwdLength": params["cardPwdLength"],
            "is_discount": params["is_discount"],
            "coupon_ctype": params["coupon_ctype"],
            "coupon_value": params["coupon_value"],
            "sms_price": params["sms_price"],
            "paymoney": str(paymoney),
            "danjia": params["danjia"],
            "is_pwdforsearch": params["is_pwdforsearch"],
            "is_coupon": params["is_coupon"],
            "price": params["price"],
            "kucun": params["kucun"],
            "select_cards": params["select_cards"],
            "feePayer": params["feePayer"],
            "fee_rate": params["fee_rate"],
            "min_fee": params["min_fee"],
            "rate": params["rate"],
            "pid": params.get("pid", "47"),
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": base_url,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "iframe",
            "Referer": product_url,
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
            "X-CSRF-TOKEN": cookie,
        }

        if "pid" not in params or not params["pid"]:
            params["pid"] = "47"

        request_url = f"{base_url}/pay/order"
        self.log(f"DEBUG 2 (request): URL={request_url}")
        self.log(f"DEBUG 2 (request): 完整请求体={order_data}")

        resp = self.session.post(
            f"{base_url}/pay/order",
            data=order_data,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        self.log(f"DEBUG 2: status={resp.status_code}")
        self.log(f"DEBUG 2: content-type={resp.headers.get('content-type', '')}")

        # 处理转义的HTML
        import html as html_module
        raw_text = resp.text
        
        if raw_text.startswith('"') and raw_text.endswith('"'):
            try:
                import json
                raw_text = json.loads(resp.text)
            except:
                pass
        
        step2_html = html_module.unescape(raw_text)
        step2_html = step2_html.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        
        soup = BeautifulSoup(step2_html, "html.parser")

        trade_no_input = soup.find("input", {"name": "trade_no"})
        if not trade_no_input or not trade_no_input.get("value"):
            if "没有可用的支付渠道" in step2_html:
                raise Exception("步骤2: 订单提交失败，该商品没有可用的支付渠道")
            elif "库存" in step2_html:
                raise Exception("步骤2: 订单提交失败，商品库存不足")
            
            match = re.search(r'trade_no["\s:=]+([\w]+)', resp.text)
            if match:
                trade_no = match.group(1)
                self.log("步骤2: 提交订单成功（从文本提取）")
                return trade_no
            raise Exception(f"步骤2: 未找到 trade_no")

        trade_no = trade_no_input.get("value")
        self.log(f"DEBUG 2: trade_no={trade_no}")
        self.log("步骤2: 提交订单成功")
        return trade_no

    def _step3_get_payment_form(self, cookie: str, orderid: str) -> dict:
        """步骤3: 获取支付表单参数"""
        full_url = f"{self.BASE_URL}/index/pay/payment.html?trade_no={orderid}&tip=0"
        
        headers = {
            "sec-ch-ua": '"Google Chrome";v="147", "Not-A.Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/index/pay/payment?trade_no={orderid}&agree=on",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
            "X-CSRF-TOKEN": cookie,
        }

        resp = self.session.get(
            full_url,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()

        import html as html_module
        raw_text = resp.text
        
        if raw_text.startswith('"') and raw_text.endswith('"'):
            try:
                import json
                raw_text = json.loads(resp.text)
            except:
                pass
        
        html_content = html_module.unescape(raw_text)
        html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        form = soup.find("form", {"name": "form1"})
        if not form:
            raise Exception(f"步骤3: 未找到form1表单")
        
        pay_params = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value")
            if name and value is not None:
                pay_params[name] = value
        
        if not pay_params:
            raise Exception("步骤3: 表单参数为空")
        
        if "sign" not in pay_params:
            raise Exception("步骤3: 表单中无sign参数")
        
        self.log(f"步骤3: 获取支付表单成功, sign={pay_params.get('sign', '')[:20]}...")
        return pay_params

    def _step4_submit_gateway(self, pay_params: dict) -> str:
        """步骤4: 提交到第三方网关，获取支付ID"""
        gateway_url = "https://www.xkku.cn/submit.php"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="147", "Not-A.Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": self.BASE_URL,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        self.log(f"步骤4请求体: money={pay_params.get('money', '')}, out_trade_no={pay_params.get('out_trade_no', '')}")
        
        resp = self.session.post(
            gateway_url,
            data=pay_params,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        import html as html_module
        html_content = html_module.unescape(resp.text)
        html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        
        import re
        match = re.search(r"/pay/qrcodepc/(\d+)/", html_content)
        if not match:
            match = re.search(r"/pay/submitpc/(\d+)/", html_content)
        
        if not match:
            raise Exception(f"步骤4: 未找到支付ID")
        
        pay_id = match.group(1)
        self.log(f"步骤4: 提交网关成功, pay_id={pay_id}")
        return pay_id

    def _step5_get_alipay_form(self, pay_id: str) -> dict:
        """步骤5: 获取支付宝表单"""
        full_url = f"https://www.xkku.cn/pay/submitpc/{pay_id}/"
        
        headers = {
            "sec-ch-ua": '"Google Chrome";v="147", "Not-A.Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "iframe",
            "Referer": f"https://www.xkku.cn/pay/qrcodepc/{pay_id}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        resp = self.session.get(
            full_url,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        import html as html_module
        html_content = html_module.unescape(resp.text)
        html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        form = soup.find("form", {"id": "alipaysubmit"})
        if not form:
            raise Exception(f"步骤5: 未找到支付宝表单")
        
        alipay_params = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value")
            if name and value is not None:
                alipay_params[name] = value
        
        if not alipay_params:
            raise Exception("步骤5: 支付宝表单参数为空")
        
        self.log(f"步骤5: 获取支付宝表单成功, method={alipay_params.get('method', '')}")
        return alipay_params

    def _step6_request_alipay_gateway(self, alipay_params: dict) -> Tuple[str, dict]:
        """步骤6: 请求支付宝网关"""
        from collections import OrderedDict
        
        gateway_url = "https://openapi.alipay.com/gateway.do?charset=UTF-8"

        ordered_params = OrderedDict()
        param_order = [
            "app_id", "version", "alipay_sdk", "charset", "format",
            "sign_type", "method", "timestamp", "notify_url",
            "return_url", "biz_content", "sign",
        ]
        for key in param_order:
            if key in alipay_params:
                ordered_params[key] = alipay_params[key]
        
        for key, val in alipay_params.items():
            if key not in ordered_params:
                ordered_params[key] = val

        ordered_params["method"] = "alipay.trade.page.pay"
        ordered_params["charset"] = "UTF-8"

        if "biz_content" in ordered_params:
            try:
                biz = json.loads(ordered_params["biz_content"])
            except (json.JSONDecodeError, TypeError):
                biz = {}
            biz["product_code"] = "FAST_INSTANT_TRADE_PAY"
            ordered_params["biz_content"] = json.dumps(biz, separators=(",", ":"), ensure_ascii=True)

        encoded_data = urlencode(ordered_params)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="147", "Not-A.Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": "https://www.xkku.cn",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "iframe",
            "Referer": "https://www.xkku.cn/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self.log(f"步骤6请求体: {encoded_data[:100]}...")

        resp = self.session.post(
            gateway_url,
            data=encoded_data,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )

        if resp.status_code not in (302, 301):
            raise Exception(f"步骤6: 预期302重定向，实际HTTP {resp.status_code}")

        location = resp.headers.get("Location")
        if not location:
            raise Exception("步骤6: 响应头中无Location字段")

        alipay_cookies = dict(resp.cookies)
        self.log("步骤6: 请求支付宝网关成功")
        return location, alipay_cookies

    def _step7_follow_redirect(self, location: str, alipay_cookies: dict) -> str:
        """步骤7: 跟随重定向"""
        all_cookies = {}
        for k, v in self.session.cookies.items():
            all_cookies[k] = v
        for k, v in alipay_cookies.items():
            all_cookies[k] = v

        resp = self.session.get(
            location,
            cookies=all_cookies,
            allow_redirects=False
        )

        if resp.status_code in [301, 302]:
            final_url = resp.headers.get("Location", resp.url)
        else:
            final_url = resp.url

        self.log("步骤7: 跟随重定向成功")
        return final_url

    def _step8_generate_qrcode(self, url: str) -> str:
        """步骤8: 生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("步骤8: 生成二维码成功")
        return qr_base64

    def query_orders(
        self,
        status: int = 1,
        start_date: str = "",
        end_date: str = "",
        pay_type: Optional[int] = None,
        order_type: Optional[int] = None
    ) -> dict:
        """查询订单列表（使用JSON API）"""
        try:
            if not self.load_cookies():
                return {
                    "success": False,
                    "message": "店铺未登录，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            # 使用JSON API接口
            api_url = f"{self.BASE_URL}/merchant/order/list"
            
            # 构建查询参数（与抓包一致）
            params = {
                "page": 1,
                "limit": 20,
                "lay": "pay",
                "goods_name": "",
                "trade_no": "",
                "channel_type": "",
                "channel_id": "",
                "status": status,
                "contact": "",
                "sms_receive": "",
                "ip": "",
                "created_at": "",
                "success_at": ""
            }
            
            # 暂不支持日期筛选（API日期格式未知）
            # if start_date and end_date:
            #     params["created_at"] = f"{start_date} - {end_date}"
            
            if pay_type is not None:
                params["channel_type"] = str(pay_type)
            
            if order_type is not None:
                params["order_type"] = str(order_type)
            
            self.log("=" * 80)
            self.log("【查询订单】请求详情:")
            self.log(f"  URL: {api_url}")
            self.log(f"  参数: {params}")
            self.log(f"  Cookies: {dict(self.session.cookies)}")
            self.log("=" * 80)

            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": f"{self.BASE_URL}/merchant/order/list",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }

            resp = self.session.get(
                api_url,
                params=params,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            
            self.log("=" * 80)
            self.log("【查询订单】响应详情:")
            self.log(f"  状态码: {resp.status_code}")
            self.log(f"  响应内容: {resp.text[:500]}")
            self.log("=" * 80)

            result = resp.json()
            
            if result.get("code") != 0:
                error_msg = result.get("msg", "获取订单失败")
                raise Exception(f"获取订单失败: {error_msg}")

            # 解析订单数据
            orders_data = result.get("data", [])
            count_items = result.get("count_items", {})
            
            self.log(f"原始订单数据: {len(orders_data)} 条")
            self.log(f"统计信息: {count_items}")
            
            # 转换订单格式，映射到OrderItem模型
            orders = []
            for order in orders_data:
                # 状态映射
                status_map = {0: "未支付", 1: "已支付", 2: "已取消", 3: "已退款"}
                status_text = status_map.get(order.get("status", 0), "未知")
                
                orders.append({
                    "order_no": order.get("trade_no", ""),
                    "order_type": "普通订单",
                    "product_name": order.get("goods_name", ""),
                    "supplier": "",
                    "payment_method": order.get("channel_text", ""),
                    "total_price": str(order.get("total_price", "0.00")),
                    "actual_price": str(order.get("total_price", "0.00")),
                    "buyer_info": order.get("contact_info", "-"),
                    "status": status_text,
                    "card_status": "已取" if order.get("status") == 1 else "未取",
                    "card_password": "",
                    "trade_time": order.get("created_at", ""),
                    "order_id": str(order.get("id", "")),
                })
            
            self.log(f"查询成功，共获取到 {len(orders)} 个订单（总计: {count_items.get('all', 0)}）")

            return {
                "success": True,
                "message": "查询成功",
                "orders": orders,
                "total": len(orders),
                "count_items": count_items
            }

        except Exception as e:
            self.log(f"查询订单失败: {str(e)}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "orders": [],
                "total": 0
            }

    def get_balance(self) -> dict:
        """查询账户余额（从商户首页解析）"""
        try:
            if not self.load_cookies():
                return {
                    "success": False,
                    "message": "店铺未登录，请在平台管理中重新登录",
                    "withdrawable": "0.00",
                    "non_withdrawable": "0.00"
                }

            # 访问商户首页获取余额信息
            merchant_url = f"{self.BASE_URL}/merchant"
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": f"{self.BASE_URL}/index/login.html",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }

            resp = self.session.get(merchant_url, headers=headers, timeout=15)
            resp.raise_for_status()

            html = unescape_html(resp.text)
            
            # 使用正则表达式提取余额和冻结金额
            # 余额：<span style="text-decoration: underline;">0.00</span>
            balance_match = re.search(r'余额：[^<]*<span[^>]*>([^<]+)</span>', html)
            # 冻结：<span style="text-decoration: underline;">0.00</span>
            frozen_match = re.search(r'冻结：[^<]*<span[^>]*>([^<]+)</span>', html)
            
            withdrawable = balance_match.group(1).strip() if balance_match else "0.00"
            non_withdrawable = frozen_match.group(1).strip() if frozen_match else "0.00"

            self.log(f"查询余额成功: 余额={withdrawable}, 冻结={non_withdrawable}")

            return {
                "success": True,
                "message": "查询成功",
                "withdrawable": withdrawable,
                "non_withdrawable": non_withdrawable
            }

        except Exception as e:
            self.log(f"查询余额失败: {str(e)}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "withdrawable": "0.00",
                "non_withdrawable": "0.00"
            }
