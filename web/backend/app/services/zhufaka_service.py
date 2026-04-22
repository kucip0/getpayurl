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


class ZhufakaService(BaseService):
    """猪发卡服务"""

    PLATFORM_CODE = "zhufaka"
    BASE_URL = "https://www.zhufaka.cn"
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
            parts = product_url.rstrip('/').split('/')
            goods_key = parts[-1]

            self.log(f"商品链接: {product_url}")
            self.log(f"提取的goods_key: {goods_key}")

            resp = self.session.get(product_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            }, timeout=15)
            resp.raise_for_status()
            self.log(f"步骤1: 访问商品页面成功")

            goods_info_url = f"{self.BASE_URL}/shopApi/Shop/goodsInfo"
            goods_info_data = {
                "goods_key": goods_key,
                "trade_no": ""
            }
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤2】获取商品信息 - 请求信息")
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
            self.log("【猪发卡-步骤2】获取商品信息 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头:")
            for k, v in resp.headers.items():
                v_display = v[:100] + "..." if len(v) > 100 else v
                self.log(f"  {k}: {v_display}")
            self.log(f"响应体:")
            self.log(resp.text)
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")

            data = result.get("data", {})
            user_info = data.get("user", {})
            
            self._goods_key = goods_key
            self._token = user_info.get("token")
            self._price = data.get("price", 0)
            self._name = data.get("name", "")
            self._contact_format = data.get("contact_format", "")
            self._query_password_status = data.get("extend", {}).get("query_password_status", 0)

            if not self._token:
                raise Exception("未获取到token")

            self.log(f"步骤2: 获取商品信息成功, token={self._token}, price={self._price}")

            price_yuan = self._price

            return {
                "success": True,
                "product_id": goods_key,
                "product_name": self._name,
                "original_price": f"{price_yuan:.2f}",
                "stock": 999,
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
            self.log("【猪发卡-步骤1】访问商品页面 - 请求信息")
            self.log(f"请求URL: {product_url}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)
            
            resp = self.session.get(product_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            }, timeout=15)
            resp.raise_for_status()
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤1】访问商品页面 - 响应信息")
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
            self.log("【猪发卡-步骤2】获取商品信息 - 请求信息")
            self.log(f"请求URL: {goods_info_url}")
            self.log(f"请求方法: POST")
            self.log(f"请求头:")
            for k, v in headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"请求体: {json.dumps(goods_info_data)}")
            self.log("=" * 80)
            
            resp = self.session.post(goods_info_url, json=goods_info_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤2】获取商品信息 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头:")
            for k, v in resp.headers.items():
                v_display = v[:100] + "..." if len(v) > 100 else v
                self.log(f"  {k}: {v_display}")
            self.log(f"响应体:")
            self.log(resp.text)
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")

            data = result.get("data", {})
            user_info = data.get("user", {})
            
            token = user_info.get("token")
            price = data.get("price", 0)
            contact_format = data.get("contact_format", "")
            query_password_status = data.get("extend", {}).get("query_password_status", 0)

            if not token:
                raise Exception("未获取到token")

            self.log(f"步骤2: 获取商品信息成功, token={token}, price={price}")

            # 步骤3: 获取支付渠道（猪发卡使用Yipay）
            channel_url = f"{self.BASE_URL}/shopApi/Shop/getUserChannel"
            channel_data = {"token": token}
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤3】获取支付渠道 - 请求信息")
            self.log(f"请求URL: {channel_url}")
            self.log(f"请求头:")
            for k, v in headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"请求体: {json.dumps(channel_data)}")
            self.log("=" * 80)

            resp = self.session.post(channel_url, json=channel_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤3】获取支付渠道 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体:")
            self.log(resp.text)
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"获取支付渠道失败: {result.get('msg', '未知错误')}")

            channels = result.get("data", [])
            yipay_channel_id = None
            for channel in channels:
                if channel.get("code") == "Yipay":
                    yipay_channel_id = channel.get("id")
                    break

            if not yipay_channel_id:
                raise Exception("未找到易支付渠道(Yipay)")

            self.log(f"步骤3: 获取支付渠道成功, channel_id={yipay_channel_id}")

            # 步骤4: 创建订单
            price_in_cents = int(new_price * 100)
            contact_phone = self._generate_phone()
            
            order_data = {
                "goods_key": goods_key,
                "quantity": 1,
                "coupon_code": "",
                "channel_id": yipay_channel_id,
                "contact": contact_phone,
                "query_password": "",
                "select_cards_ids": [],
                "extend": {"juuid": self.juuid}
            }

            self.log("=" * 80)
            self.log("【猪发卡-步骤4】创建订单 - 请求信息")
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
            self.log("【猪发卡-步骤4】创建订单 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体:")
            self.log(resp.text)
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

            # 步骤5: 访问易支付支付页面，获取submit.php表单
            # 参考request.txt：GET /payApi/Yipay/pay.html?trade_no=xxx
            pay_api_url = f"{self.BASE_URL}/payApi/Yipay/pay.html?trade_no={trade_no}"
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤5】访问易支付页面获取submit表单 - 请求信息")
            self.log(f"请求URL: {pay_api_url}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)
            
            resp = self.session.get(pay_api_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": product_url,
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤5】访问易支付页面获取submit表单 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"完整响应体:")
            self.log(resp.text)
            self.log("=" * 80)
            
            # 从HTML中提取submit.php表单
            import re
            soup = BeautifulSoup(resp.text, "html.parser")
            form = soup.find("form")
            if not form:
                raise Exception(f"未找到易支付submit表单，响应体: {resp.text}")
            
            submit_action = form.get("action", "")
            self.log(f"步骤5: 易支付submit action: {submit_action}")
            
            # 提取所有hidden input字段
            submit_form_data = {}
            for input_tag in form.find_all("input", type="hidden"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    submit_form_data[name] = value
                    self.log(f"  表单字段 {name}={value[:150]}...")
            
            if not submit_action:
                raise Exception("易支付submit表单action为空")
            
            self.log(f"步骤5: 易支付submit URL: {submit_action}")
            self.log(f"步骤5: 表单参数数量: {len(submit_form_data)}")

            # 步骤6: POST到易支付submit.php，获取支付宝表单
            # 参考request.txt：POST https://77.nkoo.cn/submit.php
            self.log("=" * 80)
            self.log("【猪发卡-步骤6】POST到易支付submit.php - 请求信息")
            self.log(f"请求URL: {submit_action}")
            self.log(f"请求方法: POST")
            self.log(f"请求头:")
            self.log(f"  Content-Type: application/x-www-form-urlencoded")
            self.log(f"  Origin: https://www.zhufaka.cn")
            self.log(f"  Referer: https://www.zhufaka.cn/")
            self.log(f"请求体参数（共{len(submit_form_data)}个）:")
            for k, v in submit_form_data.items():
                self.log(f"  {k}={v[:150]}...")
            self.log("=" * 80)

            resp = self.session.post(submit_action, data=submit_form_data, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": "https://www.zhufaka.cn/",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.zhufaka.cn",
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤6】POST到易支付submit.php - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"完整响应头:")
            for k, v in resp.headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"完整响应体:")
            self.log(resp.text)
            self.log("=" * 80)
            
            # 从响应HTML中提取支付宝表单
            soup = BeautifulSoup(resp.text, "html.parser")
            alipay_form = soup.find("form", id="alipaysubmit")
            if not alipay_form:
                alipay_form = soup.find("form")
            
            if not alipay_form:
                raise Exception(f"未找到支付宝表单，响应体: {resp.text}")
            
            alipay_action = alipay_form.get("action", "")
            self.log(f"步骤6: 支付宝表单action: {alipay_action}")
            
            # 提取所有hidden input字段
            alipay_form_data = {}
            for input_tag in alipay_form.find_all("input", type="hidden"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    alipay_form_data[name] = value
                    self.log(f"  支付宝参数 {name}={value[:150]}...")
            
            if not alipay_action:
                raise Exception("支付宝表单action为空")
            
            # 构建完整的支付宝网关URL
            if alipay_action.startswith("http"):
                alipay_gateway = alipay_action
            elif alipay_action.startswith("//"):
                alipay_gateway = f"https:{alipay_action}"
            else:
                alipay_gateway = f"https://openapi.alipay.com{alipay_action}"
            
            self.log(f"步骤6: 支付宝网关URL: {alipay_gateway}")
            self.log(f"步骤6: 支付宝参数数量: {len(alipay_form_data)}")

            # 步骤7: POST表单参数到支付宝网关，获取302重定向
            # 参考request.txt：POST /gateway.do 到 openapi.alipay.com
            self.log("=" * 80)
            self.log("【猪发卡-步骤7】POST到支付宝网关 - 请求信息")
            self.log(f"请求URL: {alipay_gateway}")
            self.log(f"请求方法: POST")
            self.log(f"请求头:")
            self.log(f"  Content-Type: application/x-www-form-urlencoded")
            self.log(f"  Origin: https://77.nkoo.cn")
            self.log(f"  Referer: https://77.nkoo.cn/")
            self.log(f"请求体参数（共{len(alipay_form_data)}个）:")
            for k, v in alipay_form_data.items():
                self.log(f"  {k}={v[:150]}...")
            self.log("=" * 80)

            resp = self.session.post(alipay_gateway, data=alipay_form_data, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": "https://77.nkoo.cn/",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://77.nkoo.cn",
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤7】POST到支付宝网关 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"完整响应头:")
            for k, v in resp.headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"完整响应体:")
            self.log(resp.text)
            self.log("=" * 80)

            # 支付宝网关返回302重定向到 mclient.alipay.com
            alipay_location = resp.headers.get("Location", "")
            
            if not alipay_location:
                raise Exception(f"支付宝网关未返回302重定向，响应状态码: {resp.status_code}")
            
            self.log(f"步骤7: 支付宝302重定向地址: {alipay_location}")

            # 步骤8: GET支付宝mclient链接，获取最终302到支付页面
            # 参考request.txt：GET /cashier/mobilepay.htm 到 mclient.alipay.com
            self.log("=" * 80)
            self.log("【猪发卡-步骤8】GET支付宝mclient链接 - 请求信息")
            self.log(f"请求URL: {alipay_location}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)

            resp = self.session.get(alipay_location, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": "https://77.nkoo.cn/",
            }, timeout=15, allow_redirects=False)
            
            self.log("=" * 80)
            self.log("【猪发卡-步骤8】GET支付宝mclient链接 - 响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"完整响应头:")
            for k, v in resp.headers.items():
                self.log(f"  {k}: {v}")
            self.log(f"完整响应体:")
            self.log(resp.text)
            self.log("=" * 80)

            # 支付宝返回302到最终支付页面
            final_location = resp.headers.get("Location", "")

            if not final_location:
                raise Exception(f"支付宝未返回重定向，响应体: {resp.text}")

            self.log(f"步骤8: 最终支付页面地址: {final_location}")

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
        """登录猪发卡平台"""
        try:
            login_url = f"{self.BASE_URL}/merchantApi/user/login"
            login_data = {
                "username": username,
                "password": password
            }
            
            self.log("=" * 80)
            self.log("【猪发卡-登录】请求信息")
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
            self.log("【猪发卡-登录】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应头Set-Cookie: {resp.headers.get('Set-Cookie', '')}")
            self.log(f"响应体: {resp.text}")
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
                    for part in cookie_part.split(";"):
                        part = part.strip()
                        if part.startswith("merchant-token="):
                            token = part.replace("merchant-token=", "")
                            break
            
            if not token:
                token = result.get("data", {}).get("merchant_token")
            
            if not token:
                raise Exception("登录成功但未获取到merchant-token")
            
            self.merchant_token = token
            self.log(f"登录成功, merchant_token={token}")
            
            self.session.cookies.set("merchant-token", token, domain="www.zhufaka.cn")
            
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
            self.load_cookies()
            
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
            self.log("【猪发卡-查询余额】请求信息")
            self.log(f"请求URL: {balance_url}")
            self.log(f"请求方法: POST")
            self.log(f"Merchant-Token: {self.merchant_token}")
            self.log("=" * 80)
            
            headers = self._get_merchant_headers()
            
            resp = self.session.post(balance_url, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【猪发卡-查询余额】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"查询余额失败: {result.get('msg', '未知错误')}")
            
            data = result.get("data", {})
            platform_data = data.get("platform", {})
            
            # available_money 和 freeze_money 已经是元为单位，不需要转换
            available_money = platform_data.get("available_money", 0)
            freeze_money = platform_data.get("freeze_money", 0)
            
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
            self.load_cookies()
            
            if not self.merchant_token:
                self.merchant_token = self.session.cookies.get("merchant-token")
            
            if not self.merchant_token:
                return {
                    "success": False,
                    "message": "商户未登录，请先在平台管理中登录"
                }
            
            numeric_id = None
            if not str(goods_id).isdigit():
                self.log(f"传入的是goods_key({goods_id})，正在查询数字ID...")
                
                list_url = f"{self.BASE_URL}/merchantApi/Goods/list"
                list_data = {
                    "current": 1,
                    "pageSize": 100,
                    "goods_type": "card",
                    "name": "",
                    "status": -1
                }
                
                headers = self._get_merchant_headers()
                resp = self.session.post(list_url, json=list_data, headers=headers, timeout=15)
                resp.raise_for_status()
                result = resp.json()
                
                if result.get("code") != 1:
                    raise Exception(f"查询商品列表失败: {result.get('msg', '未知错误')}")
                
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
            
            info_url = f"{self.BASE_URL}/merchantApi/Goods/info"
            info_data = {"id": str(numeric_id)}
            
            self.log("=" * 80)
            self.log("【猪发卡-修改价格】步骤1：获取商品信息")
            self.log(f"请求URL: {info_url}")
            self.log(f"请求体: {json.dumps(info_data)}")
            self.log("=" * 80)
            
            headers = self._get_merchant_headers()
            
            resp = self.session.post(info_url, json=info_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【猪发卡-修改价格】步骤1：商品信息响应")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")
            
            goods_info = result.get("data", {})
            
            update_url = f"{self.BASE_URL}/merchantApi/Goods/update"
            
            update_data = dict(goods_info)
            update_data["price"] = float(new_price)
            
            self.log("=" * 80)
            self.log("【猪发卡-修改价格】步骤2：提交价格修改")
            self.log(f"请求URL: {update_url}")
            self.log(f"请求体(price={new_price}): {json.dumps({k: v for k, v in update_data.items() if k == 'price'}, ensure_ascii=False)}")
            self.log("=" * 80)
            
            resp = self.session.post(update_url, json=update_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【猪发卡-修改价格】步骤2：价格修改响应")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text}")
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
            self.load_cookies()
            
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
            
            query_data = {
                "current": 1,
                "pageSize": 20,
                "status": 1,
                "trade_no": "",
                "contact": "",
                "card_no": "",
                "start_time": 0,
                "end_time": 0,
                "agent_id": None,
                "parent_id": None
            }
            
            self.log("=" * 80)
            self.log("【猪发卡-查询订单】请求信息")
            self.log(f"请求URL: {orders_url}")
            self.log(f"请求体: {json.dumps(query_data, ensure_ascii=False)}")
            self.log("=" * 80)
            
            headers = self._get_merchant_headers()
            
            resp = self.session.post(orders_url, json=query_data, headers=headers, timeout=15)
            
            self.log("=" * 80)
            self.log("【猪发卡-查询订单】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text}")
            self.log("=" * 80)
            
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"查询订单失败: {result.get('msg', '未知错误')}")
            
            data = result.get("data", {})
            total = data.get("total", 0)
            orders_list = data.get("list", [])
            
            self.log(f"查询成功，共获取到 {len(orders_list)} 个订单（总计: {total}）")
            
            orders = []
            for order in orders_list:
                status_map = {1: "待付款", 2: "已完成", 3: "已取消", 4: "已退款"}
                status_text = status_map.get(order.get("status", 0), "未知")
                
                total_amount = order.get("total_amount", 0)
                if isinstance(total_amount, (int, float)):
                    total_amount = total_amount / 100
                
                create_time = order.get("create_time", "")
                if isinstance(create_time, (int, float)) and create_time > 0:
                    from datetime import datetime
                    create_time = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S")
                
                orders.append({
                    "order_no": order.get("trade_no", ""),
                    "order_type": "普通订单",
                    "product_name": order.get("goods_name", ""),
                    "supplier": "",
                    "payment_method": "易支付",
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
