import json
import random
import string
import uuid
from typing import Tuple, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.http_client import create_session


class QiqiyunService(BaseService):
    """七七云寄售服务"""

    PLATFORM_CODE = "qiqiyun"
    BASE_URL = "https://my.77yfk.com"
    TRACKING_COOKIE = "PHPSESSID"
    FINGERPRINT_ENABLED = False

    def __init__(self, user_id: int, db):
        super().__init__(user_id, db)
        self.visitor_id = self._generate_visitor_id()
        self.juuid = self._generate_juuid()
        self.merchant_token = None  # 商户登录token

    def _get_merchant_headers(self) -> dict:
        """获取商户API请求头（包含Merchant-Token）"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": self.BASE_URL,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": f"{self.BASE_URL}/merchant/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        # 如果有merchant_token，添加到请求头
        if self.merchant_token:
            headers["Merchant-Token"] = self.merchant_token
        return headers

    def _generate_visitor_id(self) -> str:
        """生成Visitorid"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))

    def _generate_juuid(self) -> str:
        """生成juuid"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

    def _generate_phone(self) -> str:
        """生成随机中国手机号"""
        # 中国手机号前缀：13x, 15x, 18x, 19x
        prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                    '150', '151', '152', '153', '155', '156', '157', '158', '159',
                    '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
                    '190', '191', '193', '195', '196', '197', '198', '199']
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.digits, k=8))
        return prefix + suffix

    def _generate_qrcode(self, url: str) -> str:
        """生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("生成二维码成功")
        return qr_base64

    def _get_api_headers(self, content_type: str = "application/json") -> dict:
        """获取API请求头"""
        return {
            "Content-Type": content_type,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            "Accept": "application/json, text/plain, */*",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"iOS"',
            "Visitorid": self.visitor_id,
            "Origin": self.BASE_URL,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": f"{self.BASE_URL}/item/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格"""
        try:
            # 从URL中提取goods_key
            # URL格式: https://my.77yfk.com/item/9q72u4
            parts = product_url.rstrip('/').split('/')
            goods_key = parts[-1]

            self.log(f"商品链接: {product_url}")
            self.log(f"提取的goods_key: {goods_key}")

            # 步骤1: 访问商品页面，获取Cookie
            resp = self.session.get(product_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            }, timeout=15)
            resp.raise_for_status()
            self.log(f"步骤1: 访问商品页面成功")

            # 步骤2: 获取商品信息（包含token）
            goods_info_url = f"{self.BASE_URL}/shopApi/Shop/goodsInfo"
            goods_info_data = {
                "goods_key": goods_key,
                "trade_no": ""
            }
            
            self.log("=" * 80)
            self.log("【七七云-步骤2】获取商品信息 - 请求信息")
            self.log(f"请求URL: {goods_info_url}")
            self.log(f"请求方法: POST")
            self.log(f"请求头:")
            headers = self._get_api_headers()
            headers["Referer"] = product_url
            for k, v in headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"请求体: {json.dumps(goods_info_data)}")
            self.log("=" * 80)

            resp = self.session.post(goods_info_url, json=goods_info_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-步骤2】获取商品信息 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头:")
            for k, v in resp.headers.items():
                v_display = v[:100] + "..." if len(v) > 100 else v
                self.log(f"  {k}: {v_display}")
            self.log(f"响应体:")
            self.log(resp.text[:2000])
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")

            data = result.get("data", {})
            user_info = data.get("user", {})
            
            self._goods_key = goods_key
            self._token = user_info.get("token")
            self._price = data.get("price", 0)  # 单位：元（可以是小数）
            self._name = data.get("name", "")
            self._contact_format = data.get("contact_format", "")
            self._query_password_status = data.get("extend", {}).get("query_password_status", 0)

            if not self._token:
                raise Exception("未获取到token")

            self.log(f"步骤2: 获取商品信息成功, token={self._token}, price={self._price}")

            # 价格单位是元，直接使用
            price_yuan = self._price

            return {
                "success": True,
                "product_id": goods_key,
                "product_name": self._name,
                "original_price": f"{price_yuan:.2f}",
                "stock": 999,  # 七七云不返回库存，设为充足
            }

        except Exception as e:
            self.log(f"获取商品价格失败: {str(e)}")
            raise

    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单并获取支付二维码"""
        self.logs = []
        try:
            # 清除旧Cookie
            self.session.cookies.clear()
            self.log("步骤1前: 已清除从数据库加载的旧Cookie")

            # 从URL中提取goods_key
            parts = product_url.rstrip('/').split('/')
            goods_key = parts[-1]

            self.log(f"商品链接: {product_url}")
            self.log(f"提取的goods_key: {goods_key}")

            # 步骤1: 访问商品页面
            self.log("=" * 80)
            self.log("【七七云-步骤1】访问商品页面 - 请求信息")
            self.log(f"请求URL: {product_url}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)
            
            resp = self.session.get(product_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            }, timeout=15)
            resp.raise_for_status()
            
            self.log("=" * 80)
            self.log("【七七云-步骤1】访问商品页面 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头:")
            for k, v in resp.headers.items():
                v_display = v[:100] + "..." if len(v) > 100 else v
                self.log(f"  {k}: {v_display}")
            self.log(f"Cookie: {dict(self.session.cookies)}")
            self.log("=" * 80)
            
            self.log(f"步骤1: 访问商品页面成功")

            # 步骤2: 获取商品信息（包含token）
            goods_info_url = f"{self.BASE_URL}/shopApi/Shop/goodsInfo"
            goods_info_data = {
                "goods_key": goods_key,
                "trade_no": ""
            }
            
            headers = self._get_api_headers()
            headers["Referer"] = product_url
            
            self.log("=" * 80)
            self.log("【七七云-步骤2】获取商品信息 - 请求信息")
            self.log(f"请求URL: {goods_info_url}")
            self.log(f"请求方法: POST")
            self.log(f"请求头:")
            for k, v in headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"请求体: {json.dumps(goods_info_data)}")
            self.log("=" * 80)
            
            resp = self.session.post(goods_info_url, json=goods_info_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-步骤2】获取商品信息 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头:")
            for k, v in resp.headers.items():
                v_display = v[:100] + "..." if len(v) > 100 else v
                self.log(f"  {k}: {v_display}")
            self.log(f"响应体:")
            self.log(resp.text[:2000])
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")

            data = result.get("data", {})
            user_info = data.get("user", {})
            
            token = user_info.get("token")
            price = data.get("price", 0)  # 原始价格（分）
            contact_format = data.get("contact_format", "")
            query_password_status = data.get("extend", {}).get("query_password_status", 0)

            if not token:
                raise Exception("未获取到token")

            self.log(f"步骤2: 获取商品信息成功, token={token}, price={price}")

            # 步骤3: 获取支付渠道
            channel_url = f"{self.BASE_URL}/shopApi/Shop/getUserChannel"
            channel_data = {"token": token}
            
            self.log("=" * 80)
            self.log("【七七云-步骤3】获取支付渠道 - 请求信息")
            self.log(f"请求URL: {channel_url}")
            self.log(f"请求头:")
            for k, v in headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"请求体: {json.dumps(channel_data)}")
            self.log("=" * 80)

            resp = self.session.post(channel_url, json=channel_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-步骤3】获取支付渠道 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体:")
            self.log(resp.text[:2000])
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"获取支付渠道失败: {result.get('msg', '未知错误')}")

            channels = result.get("data", [])
            alipay_channel_id = None
            for channel in channels:
                if channel.get("code") == "AlipayH5":
                    alipay_channel_id = channel.get("id")
                    break

            if not alipay_channel_id:
                raise Exception("未找到支付宝支付渠道(AlipayH5)")

            self.log(f"步骤3: 获取支付渠道成功, channel_id={alipay_channel_id}")

            # 步骤4: 创建订单
            # 价格转换为分（new_price是元）
            price_in_cents = int(new_price * 100)
            contact_phone = self._generate_phone()
            
            order_data = {
                "goods_key": goods_key,
                "quantity": 1,
                "coupon_code": "",
                "channel_id": alipay_channel_id,
                "contact": contact_phone,  # 随机生成手机号
                "query_password": "",
                "select_cards_ids": [],
                "extend": {"juuid": self.juuid}
            }

            self.log("=" * 80)
            self.log("【七七云-步骤4】创建订单 - 请求信息")
            self.log(f"请求URL: {self.BASE_URL}/shopApi/Pay/order")
            self.log(f"请求头:")
            for k, v in headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"请求体: {json.dumps(order_data)}")
            self.log("=" * 80)

            resp = self.session.post(
                f"{self.BASE_URL}/shopApi/Pay/order",
                json=order_data,
                headers=headers,
                timeout=15
            )
            
            self.log("=" * 80)
            self.log("【七七云-步骤4】创建订单 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体:")
            self.log(resp.text[:2000])
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"创建订单失败: {result.get('msg', '未知错误')}")

            order_data_resp = result.get("data", {})
            trade_no = order_data_resp.get("trade_no")
            payurl = order_data_resp.get("payurl")

            if not trade_no or not payurl:
                raise Exception(f"创建订单成功但未返回trade_no或payurl: {result}")

            self.log(f"步骤4: 创建订单成功, trade_no={trade_no}, payurl={payurl}")

            # 步骤5: 跟随重定向获取支付宝网关
            self.log("=" * 80)
            self.log("【七七云-步骤5】请求payurl获取重定向 - 请求信息")
            self.log(f"请求URL: {payurl}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)
            
            resp = self.session.get(payurl, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": product_url,
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【七七云-步骤5】请求payurl获取重定向 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头Location: {resp.headers.get('Location', '')}")
            self.log("=" * 80)
            
            # 获取Location
            location = resp.headers.get("Location", "")

            if not location:
                raise Exception("未获取到重定向地址")

            # 构建完整的支付URL
            if location.startswith("/"):
                payment_url = f"{self.BASE_URL}{location}"
            else:
                payment_url = location

            self.log(f"步骤5: 完整支付URL: {payment_url}")

            # 步骤6: 请求支付页面，获取支付宝表单
            self.log("=" * 80)
            self.log("【七七云-步骤6】请求支付页面获取支付宝表单 - 请求信息")
            self.log(f"请求URL: {payment_url}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)
            
            resp = self.session.get(payment_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": product_url,
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【七七云-步骤6】请求支付页面获取支付宝表单 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体(前500字符):")
            self.log(resp.text[:500])
            self.log("=" * 80)
            
            # 从HTML中提取表单action和所有hidden input参数
            soup = BeautifulSoup(resp.text, "html.parser")
            form = soup.find("form")
            if not form:
                raise Exception("未找到支付宝支付表单")
            
            action = form.get("action", "")
            self.log(f"步骤6: 支付宝表单action: {action}")
            
            # 提取所有hidden input字段
            form_data = {}
            for input_tag in form.find_all("input", type="hidden"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    form_data[name] = value
                    self.log(f"  表单字段 {name}={value[:80]}...")
            
            if not action:
                raise Exception("支付宝表单action为空")
            
            # 构建完整的支付宝网关URL
            if action.startswith("http"):
                alipay_gateway = action
            elif action.startswith("//"):
                alipay_gateway = f"https:{action}"
            else:
                alipay_gateway = f"https://openapi.alipay.com{action}"
            
            self.log(f"步骤6: 支付宝网关URL: {alipay_gateway}")
            
            # 步骤7: POST到支付宝网关
            self.log("=" * 80)
            self.log("【七七云-步骤7】POST到支付宝网关 - 请求信息")
            self.log(f"请求URL: {alipay_gateway}")
            self.log(f"请求方法: POST")
            self.log(f"请求体(前500字符):")
            # 只打印部分表单数据，避免过长
            form_data_preview = {k: (v[:100] + "..." if len(v) > 100 else v) for k, v in form_data.items()}
            self.log(f"{json.dumps(form_data_preview, ensure_ascii=False)}")
            self.log("=" * 80)
            
            resp = self.session.post(alipay_gateway, data=form_data, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": f"{self.BASE_URL}/",
                "Content-Type": "application/x-www-form-urlencoded",
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【七七云-步骤7】POST到支付宝网关 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头Location: {resp.headers.get('Location', '')}")
            self.log("=" * 80)
            
            alipay_location = resp.headers.get("Location", "")
            
            if not alipay_location:
                raise Exception("支付宝网关未返回重定向")
            
            # 步骤8: 跟随支付宝重定向获取最终二维码地址
            self.log("=" * 80)
            self.log("【七七云-步骤8】请求支付宝客户端获取最终二维码 - 请求信息")
            self.log(f"请求URL: {alipay_location}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)
            
            resp = self.session.get(alipay_location, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": f"{self.BASE_URL}/",
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【七七云-步骤8】请求支付宝客户端获取最终二维码 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头Location: {resp.headers.get('Location', '')}")
            self.log("=" * 80)
            
            final_location = resp.headers.get("Location", "")
            
            if not final_location:
                # 如果还是没有location，使用alipay_location
                final_location = alipay_location
                self.log(f"警告: 未获取到最终location，使用步骤7的location")

            self.log(f"步骤8: 最终二维码地址: {final_location}")

            # 步骤9: 生成二维码
            qr_base64 = self._generate_qrcode(final_location)
            self.log(f"二维码生成成功, order_no={trade_no}")

            return {
                "success": True,
                "order_id": trade_no,
                "qr_code_base64": qr_base64,
                "payment_url": final_location,
                "logs": self.logs,
            }

        except Exception as e:
            self.log(f"订单处理失败: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "logs": self.logs,
            }

    def login(self, username: str, password: str, verify_code: str = "", csrf_token: str = "") -> dict:
        """登录七七云平台"""
        try:
            login_url = f"{self.BASE_URL}/merchantApi/user/login"
            login_data = {
                "username": username,
                "password": password
            }
            
            self.log("=" * 80)
            self.log("【七七云-登录】请求信息")
            self.log(f"请求URL: {login_url}")
            self.log(f"请求方法: POST")
            self.log(f"请求体: {json.dumps(login_data)}")
            self.log("=" * 80)
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Origin": self.BASE_URL,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": f"{self.BASE_URL}/merchant/login/",
            }
            
            resp = self.session.post(login_url, json=login_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-登录】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头Set-Cookie: {resp.headers.get('Set-Cookie', '')}")
            self.log(f"响应体: {resp.text[:500]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"登录失败: {result.get('msg', '未知错误')}")
            
            # 从响应头Set-Cookie中提取merchant-token
            set_cookie = resp.headers.get("Set-Cookie", "")
            token = None
            for cookie_part in set_cookie.split(","):
                if "merchant-token=" in cookie_part:
                    # 提取token值
                    for part in cookie_part.split(";"):
                        part = part.strip()
                        if part.startswith("merchant-token="):
                            token = part.replace("merchant-token=", "")
                            break
            
            # 如果从Set-Cookie没找到，尝试从响应data中获取
            if not token:
                token = result.get("data", {}).get("merchant_token")
            
            if not token:
                raise Exception("登录成功但未获取到merchant-token")
            
            self.merchant_token = token
            self.log(f"登录成功, merchant_token={token}")
            
            # 保存token到cookies（以便load_cookies/save_cookies机制可以管理）
            self.session.cookies.set("merchant-token", token, domain="my.77yfk.com")
            
            return {
                "success": True,
                "message": "登录成功",
                "shop_name": username,
            }
            
        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise

    def get_balance(self) -> dict:
        """查询账户余额"""
        try:
            # 加载Cookies（包含merchant_token）
            self.load_cookies()
            
            # 从cookies中提取merchant_token
            if not self.merchant_token:
                self.merchant_token = self.session.cookies.get("merchant-token")
            
            if not self.merchant_token:
                return {
                    "success": False,
                    "message": "商户未登录，请先在平台管理中登录",
                    "withdrawable": "0.00",
                    "non_withdrawable": "0.00"
                }
            
            balance_url = f"{self.BASE_URL}/merchantApi/wallet/info"
            
            self.log("=" * 80)
            self.log("【七七云-查询余额】请求信息")
            self.log(f"请求URL: {balance_url}")
            self.log(f"请求方法: POST")
            self.log(f"Merchant-Token: {self.merchant_token}")
            self.log("=" * 80)
            
            headers = self._get_merchant_headers()
            
            resp = self.session.post(balance_url, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-查询余额】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text[:500]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"查询余额失败: {result.get('msg', '未知错误')}")
            
            # 解析余额信息
            data = result.get("data", {})
            platform_data = data.get("platform", {})
            
            available_money = platform_data.get("available_money", 0)
            freeze_money = platform_data.get("freeze_money", 0)
            
            # 转换为元（API返回的可能是分）
            if isinstance(available_money, (int, float)):
                available_money = available_money / 100
            if isinstance(freeze_money, (int, float)):
                freeze_money = freeze_money / 100
            
            self.log(f"查询余额成功: 可用余额={available_money}, 冻结金额={freeze_money}")
            
            return {
                "success": True,
                "message": "查询成功",
                "withdrawable": f"{available_money:.2f}",
                "non_withdrawable": f"{freeze_money:.2f}"
            }
            
        except Exception as e:
            self.log(f"查询余额失败: {str(e)}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "withdrawable": "0.00",
                "non_withdrawable": "0.00"
            }

    def modify_goods_price(self, goods_id: str, new_price: str) -> dict:
        """修改商品价格"""
        try:
            # 加载Cookies（包含merchant_token）
            self.load_cookies()
            
            # 从cookies中提取merchant_token
            if not self.merchant_token:
                self.merchant_token = self.session.cookies.get("merchant-token")
            
            if not self.merchant_token:
                return {
                    "success": False,
                    "message": "商户未登录，请先在平台管理中登录"
                }
            
            # 如果传入的是goods_key（字符串如9q72u4），需要先查询获取数字ID
            numeric_id = None
            if not str(goods_id).isdigit():
                # 这是goods_key，需要查询获取数字ID
                self.log(f"传入的是goods_key({goods_id})，正在查询数字ID...")
                
                # 调用商户商品列表API查找
                list_url = f"{self.BASE_URL}/merchantApi/Goods/list"
                list_data = {
                    "current": 1,
                    "pageSize": 100,
                    "goods_type": "card",
                    "name": "",
                    "status": -1  # 所有状态
                }
                
                headers = self._get_merchant_headers()
                resp = self.session.post(list_url, json=list_data, headers=headers, timeout=15)
                resp.raise_for_status()
                result = resp.json()
                
                if result.get("code") != 1:
                    raise Exception(f"查询商品列表失败: {result.get('msg', '未知错误')}")
                
                # 查找匹配的goods_key
                goods_list = result.get("data", {}).get("list", [])
                for item in goods_list:
                    if item.get("goods_key") == goods_id:
                        numeric_id = item.get("id")
                        self.log(f"找到商品 {goods_id} 对应的数字ID: {numeric_id}")
                        break
                
                if not numeric_id:
                    raise Exception(f"未找到goods_key={goods_id}对应的数字ID")
            else:
                numeric_id = int(goods_id)
            
            # 步骤1: 获取商品完整信息
            info_url = f"{self.BASE_URL}/merchantApi/Goods/info"
            info_data = {"id": str(numeric_id)}
            
            self.log("=" * 80)
            self.log("【七七云-修改价格】步骤1：获取商品信息")
            self.log(f"请求URL: {info_url}")
            self.log(f"请求体: {json.dumps(info_data)}")
            self.log("=" * 80)
            
            headers = self._get_merchant_headers()
            
            resp = self.session.post(info_url, json=info_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-修改价格】步骤1：商品信息响应")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text[:500]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")
            
            goods_info = result.get("data", {})
            
            # 步骤2: 修改价格
            update_url = f"{self.BASE_URL}/merchantApi/Goods/update"
            
            # 构建完整的更新数据（保留所有原始字段，只修改price）
            update_data = dict(goods_info)
            # price单位转换为元（如果原始是分）
            update_data["price"] = float(new_price)
            
            self.log("=" * 80)
            self.log("【七七云-修改价格】步骤2：提交价格修改")
            self.log(f"请求URL: {update_url}")
            self.log(f"请求体(price={new_price}): {json.dumps({k: v for k, v in update_data.items() if k == 'price'}, ensure_ascii=False)}")
            self.log("=" * 80)
            
            resp = self.session.post(update_url, json=update_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-修改价格】步骤2：价格修改响应")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text[:500]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"修改价格失败: {result.get('msg', '未知错误')}")
            
            self.log(f"修改价格成功: goods_id={goods_id}, new_price={new_price}")
            
            return {
                "success": True,
                "message": f"价格已修改为 ¥{new_price}",
                "goods_id": goods_id,
                "new_price": new_price,
            }
            
        except Exception as e:
            self.log(f"修改价格失败: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    def query_orders(
        self,
        status: int = 1,
        start_date: str = "",
        end_date: str = "",
        pay_type: Optional[int] = None,
        order_type: Optional[int] = None
    ) -> dict:
        """查询订单列表"""
        try:
            # 加载Cookies（包含merchant_token）
            self.load_cookies()
            
            # 从cookies中提取merchant_token
            if not self.merchant_token:
                self.merchant_token = self.session.cookies.get("merchant-token")
            
            if not self.merchant_token:
                return {
                    "success": False,
                    "message": "商户未登录，请先在平台管理中登录",
                    "orders": [],
                    "total": 0
                }
            
            orders_url = f"{self.BASE_URL}/merchantApi/order/list"
            
            # 构建查询参数（status=1查询已完成订单）
            query_data = {
                "current": 1,
                "pageSize": 20,
                "status": 1,  # 查询已完成订单
                "trade_no": "",
                "contact": "",
                "card_no": "",
                "start_time": 0,
                "end_time": 0,
                "agent_id": None,
                "parent_id": None
            }
            
            self.log("=" * 80)
            self.log("【七七云-查询订单】请求信息")
            self.log(f"请求URL: {orders_url}")
            self.log(f"请求体: {json.dumps(query_data, ensure_ascii=False)}")
            self.log("=" * 80)
            
            headers = self._get_merchant_headers()
            
            resp = self.session.post(orders_url, json=query_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【七七云-查询订单】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体(前1000字符): {resp.text[:1000]}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"查询订单失败: {result.get('msg', '未知错误')}")
            
            # 解析订单数据
            data = result.get("data", {})
            total = data.get("total", 0)
            orders_list = data.get("list", [])
            
            self.log(f"查询成功，共获取到 {len(orders_list)} 个订单（总计: {total}）")
            
            # 转换订单格式
            orders = []
            for order in orders_list:
                # 状态映射
                status_map = {1: "待付款", 2: "已完成", 3: "已取消", 4: "已退款"}
                status_text = status_map.get(order.get("status", 0), "未知")
                
                # 计算订单金额（分转元）
                total_amount = order.get("total_amount", 0)
                if isinstance(total_amount, (int, float)):
                    total_amount = total_amount / 100
                
                # 时间戳转换
                create_time = order.get("create_time", "")
                if isinstance(create_time, (int, float)) and create_time > 0:
                    from datetime import datetime
                    create_time = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S")
                
                orders.append({
                    "order_no": order.get("trade_no", ""),
                    "order_type": "普通订单",
                    "product_name": order.get("goods_name", ""),
                    "supplier": "",
                    "payment_method": "支付宝",  # 七七云默认支付宝
                    "total_price": f"{total_amount:.2f}",
                    "actual_price": f"{total_amount:.2f}",
                    "buyer_info": "-",
                    "status": status_text,
                    "card_status": "已取" if order.get("status") == 2 else "未取",
                    "card_password": "",
                    "trade_time": create_time,
                    "order_id": order.get("trade_no", ""),
                })
            
            self.log(f"订单转换完成，共 {len(orders)} 条")
            
            return {
                "success": True,
                "message": "查询成功",
                "orders": orders,
                "total": len(orders),
            }
            
        except Exception as e:
            self.log(f"查询订单失败: {str(e)}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "orders": [],
                "total": 0
            }
