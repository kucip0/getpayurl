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

    def _generate_visitor_id(self) -> str:
        """生成Visitorid"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))

    def _generate_juuid(self) -> str:
        """生成juuid"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

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
            self._price = data.get("price", 0)  # 单位：分
            self._name = data.get("name", "")
            self._contact_format = data.get("contact_format", "")
            self._query_password_status = data.get("extend", {}).get("query_password_status", 0)

            if not self._token:
                raise Exception("未获取到token")

            self.log(f"步骤2: 获取商品信息成功, token={self._token}, price={self._price}")

            # 转换价格为元
            price_yuan = self._price / 100

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
            # 从URL中提取goods_key
            parts = product_url.rstrip('/').split('/')
            goods_key = parts[-1]

            # 步骤1: 访问商品页面
            resp = self.session.get(product_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            }, timeout=15)
            resp.raise_for_status()
            self.log(f"步骤1: 访问商品页面成功")

            # 步骤2: 获取商品信息（包含token）
            goods_info_url = f"{self.BASE_URL}/shopApi/Shop/goodsInfo"
            goods_info_data = {
                "goods_key": goods_key,
                "trade_no": ""
            }
            
            headers = self._get_api_headers()
            headers["Referer"] = product_url
            
            resp = self.session.post(goods_info_url, json=goods_info_data, headers=headers, timeout=15)
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

            self.log(f"步骤2: 获取商品信息成功, token={token}")

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
            
            order_data = {
                "goods_key": goods_key,
                "quantity": 1,
                "coupon_code": "",
                "channel_id": alipay_channel_id,
                "contact": "",  # 联系方式，根据contact_format可能需要
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

            self.log(f"步骤4: 创建订单成功, trade_no={trade_no}")

            # 步骤5: 跟随重定向获取支付宝网关
            self.log(f"步骤5: 请求payurl: {payurl}")
            
            # 关闭自动重定向，手动处理
            resp = self.session.get(payurl, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": product_url,
            }, timeout=15, allow_redirects=False)

            self.log(f"步骤5响应状态码: {resp.status_code}")
            
            # 获取Location
            location = resp.headers.get("Location", "")
            self.log(f"步骤5重定向地址: {location}")

            if not location:
                raise Exception("未获取到重定向地址")

            # 构建完整的支付URL
            if location.startswith("/"):
                payment_url = f"{self.BASE_URL}{location}"
            else:
                payment_url = location

            self.log(f"步骤5: 完整支付URL: {payment_url}")

            # 步骤6: 请求支付页面，获取支付宝表单
            resp = self.session.get(payment_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": product_url,
            }, timeout=15, allow_redirects=False)

            self.log(f"步骤6响应状态码: {resp.status_code}")
            self.log(f"步骤6响应头Location: {resp.headers.get('Location', '')}")

            # 获取支付宝重定向地址
            alipay_location = resp.headers.get("Location", "")
            
            if not alipay_location:
                # 如果没有重定向，尝试从HTML中提取表单
                soup = BeautifulSoup(resp.text, "html.parser")
                form = soup.find("form")
                if form:
                    action = form.get("action", "")
                    self.log(f"从HTML中提取到支付宝表单action: {action}")
                    # 直接返回这个URL作为二维码
                    return {
                        "success": True,
                        "qr_code_url": action if action.startswith("http") else f"https:{action}",
                        "payment_url": action if action.startswith("http") else f"https:{action}",
                        "order_no": trade_no,
                    }
                raise Exception("未获取到支付宝重定向地址")

            self.log(f"步骤6: 支付宝重定向地址: {alipay_location}")

            # 步骤7: 跟随支付宝重定向
            if alipay_location.startswith("/"):
                alipay_url = f"https://mclient.alipay.com{alipay_location}"
            elif alipay_location.startswith("http"):
                alipay_url = alipay_location
            else:
                alipay_url = f"https://{alipay_location}"

            resp = self.session.get(alipay_url, headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Referer": f"{self.BASE_URL}/",
            }, timeout=15, allow_redirects=False)

            final_location = resp.headers.get("Location", "")
            self.log(f"步骤7: 最终二维码地址: {final_location}")

            if not final_location:
                # 如果还是没有，使用上一步的URL
                final_location = alipay_url

            self.log(f"二维码生成成功, order_no={trade_no}")

            return {
                "success": True,
                "qr_code_url": final_location,
                "payment_url": final_location,
                "order_no": trade_no,
            }

        except Exception as e:
            self.log(f"订单处理失败: {str(e)}")
            raise
