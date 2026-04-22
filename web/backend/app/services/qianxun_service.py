import json
import random
import re
import string
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.http_client import create_session


class QianxunService(BaseService):
    """千寻寄售服务"""

    PLATFORM_CODE = "qianxun"
    BASE_URL = "https://www.qianxun1688.com"
    TRACKING_COOKIE = "server_name_session"
    FINGERPRINT_ENABLED = False

    def __init__(self, user_id: int, db):
        super().__init__(user_id, db)
        self.merchant_token = None
        # 清除 create_session 默认 headers 中可能干扰消费者端请求的项
        self.session.headers.pop("X-Requested-With", None)
        self.session.headers.pop("Content-Type", None)

    def _generate_phone(self) -> str:
        """生成随机中国手机号"""
        prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                    '150', '151', '152', '153', '155', '156', '157', '158', '159',
                    '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
                    '190', '191', '193', '195', '196', '197', '198', '199']
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.digits, k=8))
        return prefix + suffix

    def _get_mobile_page_headers(self, referer: str = "") -> dict:
        """获取移动端页面请求头（步骤1访问商品详情页）"""
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"iOS"',
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        if referer:
            headers["Referer"] = referer
        return headers

    def _get_mobile_headers(self, referer: str = "") -> dict:
        """获取移动端API请求头（步骤2-4接口调用）"""
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            "Accept": "application/json, text/plain, */*",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"iOS"',
            "Origin": self.BASE_URL,
            "Content-Type": "application/json",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        if referer:
            headers["Referer"] = referer
        return headers

    def _get_desktop_headers(self, referer: str = "", content_type: str = "") -> dict:
        """获取桌面端请求头（支付宝流程步骤5-7）"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        if referer:
            headers["Referer"] = referer
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _get_merchant_headers(self) -> dict:
        """获取商户API请求头（包含Authorization）"""
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
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        if self.merchant_token:
            headers["Authorization"] = f"Bearer {self.merchant_token}"
        return headers

    def _extract_from_shop_site(self, result: dict) -> tuple:
        """从 shop_site 响应中提取 goodid, cateid, channels"""
        data = result.get("data", {})
        goodid = None
        cateid = None
        channels = []

        self.log(f"shop_site data 结构: {json.dumps(data, ensure_ascii=False)[:2000]}")

        # 优先尝试常见结构（基于真实响应推断）
        goods_info = data.get("goods") or data.get("good") or data.get("product") or data.get("goodsList")
        if isinstance(goods_info, dict):
            goodid = goods_info.get("goodid") or goods_info.get("id") or goods_info.get("goods_id")
            cateid = goods_info.get("cateid") or goods_info.get("cate_id") or goods_info.get("category_id")
        elif isinstance(goods_info, list) and goods_info:
            goodid = goods_info[0].get("goodid") or goods_info[0].get("id") or goods_info[0].get("goods_id")
            cateid = goods_info[0].get("cateid") or goods_info[0].get("cate_id") or goods_info[0].get("category_id")

        # 提取支付渠道列表（千寻寄售在 pay_chanel 中，注意拼写）
        for key in ["pay_chanel", "pay_types", "channels", "pay_list", "payments"]:
            val = data.get(key)
            if isinstance(val, list):
                channels = val
                break
            # 尝试在子对象中查找
            for sub in [data.get("shop"), data.get("goods"), data.get("good")]:
                if isinstance(sub, dict) and isinstance(sub.get(key), list):
                    channels = sub[key]
                    break
            if channels:
                break

        self.log(f"从shop_site提取: goodid={goodid}, cateid={cateid}, 渠道数量={len(channels)}")
        if channels:
            for ch in channels:
                self.log(f"  渠道: {ch}")

        return goodid, cateid, channels

    def _log_full_request(self, method: str, url: str, headers: dict, body=None, cookies=None):
        """打印完整的请求信息（含请求头、body、cookies）"""
        self.log("-" * 60)
        self.log(f"[REQUEST] {method} {url}")
        self.log("-" * 60)
        self.log("[REQUEST HEADERS]:")
        for k, v in sorted(headers.items()):
            self.log(f"  {k}: {v}")
        if cookies:
            self.log("[REQUEST COOKIES]:")
            if isinstance(cookies, dict):
                for k, v in cookies.items():
                    self.log(f"  {k}={v}")
            else:
                self.log(f"  {cookies}")
        if body is not None:
            if isinstance(body, dict):
                self.log(f"[REQUEST BODY]: {json.dumps(body, ensure_ascii=False)}")
            else:
                self.log(f"[REQUEST BODY]: {body}")
        self.log("-" * 60)

    def _fetch_goods_core(self, product_url: str) -> dict:
        """获取商品核心信息（步骤1-3，get_product_price和submit_order共用）"""
        parts = product_url.rstrip('/').split('/')
        goods_key = parts[-1]

        # 清除商户cookie，避免干扰消费者端接口
        removed = self.session.cookies.pop("merchant-token", None)
        self.log(f"【千寻寄售】清除merchant-token: {'已清除' if removed else '无此cookie'}")
        self.log(f"当前session cookies: {dict(self.session.cookies)}")

        # 步骤1: 访问商品页面获取初始cookie
        self.log("=" * 80)
        self.log("【千寻寄售】步骤1: 访问商品页面")
        headers1 = self._get_mobile_page_headers()
        self._log_full_request("GET", product_url, headers1, cookies=dict(self.session.cookies))
        resp = self.session.get(product_url, headers=headers1, timeout=15)
        resp.raise_for_status()

        # 打印完整响应头（特别是所有Set-Cookie）
        self.log("[步骤1 响应头]:")
        for k, v in resp.headers.items():
            self.log(f"  {k}: {v}")

        # 从HTML中搜索JS设置的cookie（document.cookie=...）
        js_cookies_found = []
        if "document.cookie" in resp.text:
            pattern = re.compile(r'document\.cookie\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
            for match in pattern.findall(resp.text):
                js_cookies_found.append(match)
                self.log(f"[步骤1 发现JS设置cookie]: {match}")
                if "=" in match:
                    ck_name, ck_val = match.split("=", 1)
                    self.session.cookies.set(ck_name.strip(), ck_val.strip(), domain="www.qianxun1688.com")

        # 也尝试从原始响应头中提取所有Set-Cookie
        raw_set_cookies = resp.headers.get_all("Set-Cookie") if hasattr(resp.headers, "get_all") else []
        if not raw_set_cookies and "Set-Cookie" in resp.headers:
            raw_set_cookies = [resp.headers["Set-Cookie"]]
        if raw_set_cookies:
            self.log("[步骤1 原始Set-Cookie]:")
            for h in raw_set_cookies:
                self.log(f"  {h}")

        self.log(f"步骤1完成后 cookies={dict(self.session.cookies)}")

        # 步骤2: 获取店铺/商品信息
        shop_site_url = f"{self.BASE_URL}/shopapi/shop/shop_site"
        shop_site_payload = {"store_key": goods_key, "shop_type": "goods"}
        headers2 = self._get_mobile_headers(referer=product_url)

        self.log("=" * 80)
        self.log("【千寻寄售】步骤2: 获取店铺信息")
        # 使用 requests.Request 查看 prepared request 的最终内容
        req = requests.Request("POST", shop_site_url, json=shop_site_payload, headers=headers2, cookies=self.session.cookies)
        prep = self.session.prepare_request(req)
        self._log_full_request("POST", shop_site_url, dict(prep.headers), body=shop_site_payload, cookies=dict(self.session.cookies))

        resp = self.session.post(
            shop_site_url,
            json=shop_site_payload,
            headers=headers2,
            timeout=15
        )
        resp.raise_for_status()
        result = resp.json()

        # 打印步骤2响应头（检查Set-Cookie）
        self.log("[步骤2 响应头]:")
        for k, v in resp.headers.items():
            self.log(f"  {k}: {v}")

        # 从步骤2响应中提取 s6ed1c7d3（即使请求失败，服务器也可能设置此cookie）
        raw_set_cookies2 = resp.headers.get_all("Set-Cookie") if hasattr(resp.headers, "get_all") else []
        if not raw_set_cookies2 and "Set-Cookie" in resp.headers:
            raw_set_cookies2 = [resp.headers["Set-Cookie"]]
        s6_cookie_extracted = None
        for h in raw_set_cookies2:
            if "s6ed1c7d3=" in h:
                s6_cookie_extracted = h.split("s6ed1c7d3=")[1].split(";")[0].strip()
                self.session.cookies.set("s6ed1c7d3", s6_cookie_extracted, domain="www.qianxun1688.com")
                self.log(f"[步骤2 提取到s6ed1c7d3]: {s6_cookie_extracted}")
                break

        self.log(f"步骤2首次响应: {json.dumps(result, ensure_ascii=False)[:1500]}")

        # 如果失败且提取到了 s6ed1c7d3，重试一次
        if result.get("code") != 1 and s6_cookie_extracted:
            self.log(f"步骤2首次失败({result.get('msg')})，但获取到s6ed1c7d3，正在重试...")
            self._log_full_request("POST(retry)", shop_site_url, headers2, body=shop_site_payload, cookies=dict(self.session.cookies))
            resp = self.session.post(
                shop_site_url,
                json=shop_site_payload,
                headers=headers2,
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()
            self.log(f"步骤2重试响应: {json.dumps(result, ensure_ascii=False)[:1500]}")

        if result.get("code") != 1:
            raise Exception(f"获取店铺信息失败: {result.get('msg', '未知错误')}")

        goodid, cateid, channels = self._extract_from_shop_site(result)

        if not goodid:
            raise Exception("未能从店铺信息中提取到 goodid")

        # 步骤3: 获取商品详细信息（包含价格、token）
        goods_info_url = f"{self.BASE_URL}/shopapi/shop/goods_info"
        goods_info_payload = {"goodid": int(goodid) if str(goodid).isdigit() else goodid}
        headers3 = self._get_mobile_headers(referer=product_url)

        self.log("=" * 80)
        self.log("【千寻寄售】步骤3: 获取商品信息")
        self._log_full_request("POST", goods_info_url, headers3, body=goods_info_payload, cookies=dict(self.session.cookies))

        resp = self.session.post(
            goods_info_url,
            json=goods_info_payload,
            headers=headers3,
            timeout=15
        )
        resp.raise_for_status()
        result = resp.json()
        self.log(f"步骤3响应: {json.dumps(result, ensure_ascii=False)[:1500]}")

        if result.get("code") != 1:
            raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")

        data = result.get("data", {})
        return {
            "goods_key": goods_key,
            "goodid": goodid,
            "cateid": cateid,
            "channels": channels,
            "token": data.get("token"),
            "user_id": data.get("user_id"),
            "price": data.get("price", "0.00"),
            "name": data.get("name", ""),
            "stock": data.get("kucun", "0"),
        }

    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格"""
        try:
            self.log(f"商品链接: {product_url}")
            info = self._fetch_goods_core(product_url)

            price_val = float(info["price"]) if info["price"] else 0.0
            stock_val = int(info["stock"]) if info["stock"] else 0

            self.log(f"获取价格成功: name={info['name']}, price={price_val}, stock={stock_val}")

            return {
                "success": True,
                "product_id": info["goods_key"],
                "product_name": info["name"],
                "original_price": price_val,
                "stock": stock_val,
            }

        except Exception as e:
            self.log(f"获取商品价格失败: {str(e)}")
            raise

    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单并获取支付二维码"""
        self.logs = []
        try:
            self.log(f"商品链接: {product_url}")

            # 步骤1-3: 获取商品核心信息（与get_product_price共用）
            info = self._fetch_goods_core(product_url)
            goods_key = info["goods_key"]
            goodid = info["goodid"]
            cateid = info["cateid"]
            channels = info["channels"]
            token = info["token"]
            user_id = info["user_id"]

            if not token:
                raise Exception("未获取到token")
            if not user_id:
                raise Exception("未获取到user_id")

            # 选择 pay_type=2 的支付宝渠道
            pid = None
            for ch in channels:
                if ch.get("pay_type") == 2 or ch.get("type") == 2 or "支付宝" in str(ch.get("show_name", "")):
                    pid = ch.get("channel_id")
                    self.log(f"选中支付宝渠道: id={pid}, name={ch.get('show_name')}")
                    break

            if not pid and channels:
                pid = channels[0].get("channel_id")
                self.log(f"未找到pay_type=2，使用第一个渠道: id={pid}")

            if not pid:
                raise Exception("未找到可用支付渠道")

            # 步骤4: 创建订单
            order_url = f"{self.BASE_URL}/shopapi/pay/order"
            contact_phone = self._generate_phone()
            order_payload = {
                "cateid": int(cateid) if cateid and str(cateid).isdigit() else 0,
                "types": "shop",
                "goodid": int(goodid) if str(goodid).isdigit() else goodid,
                "contact": contact_phone,
                "userid": user_id,
                "token": token,
                "pid": int(pid) if str(pid).isdigit() else pid,
                "quantity": 1,
                "is_coupon": 0,
            }

            self.log("=" * 80)
            self.log("【千寻寄售-下单】步骤4: 创建订单")
            self.log(f"请求URL: {order_url}")
            self.log(f"请求体: {json.dumps(order_payload)}")

            resp = self.session.post(
                order_url,
                json=order_payload,
                headers=self._get_mobile_headers(referer=product_url),
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()
            self.log(f"步骤4响应: {json.dumps(result, ensure_ascii=False)}")

            if result.get("code") != 1:
                raise Exception(f"创建订单失败: {result.get('msg', '未知错误')}")

            order_data = result.get("data", {})
            trade_no = order_data.get("order", {}).get("trade_no")
            pay_urll = order_data.get("pay_urll")

            if not trade_no:
                raise Exception("创建订单成功但未返回trade_no")

            self.log(f"步骤4成功: trade_no={trade_no}, pay_urll={pay_urll}")

            # 步骤5: 获取支付宝表单（切换为桌面UA）
            payment_url = f"{self.BASE_URL}/index/pay/payment"
            payment_params = {"trade_no": trade_no, "agree": "on"}

            self.log("=" * 80)
            self.log("【千寻寄售-下单】步骤5: 获取支付宝表单")
            self.log(f"请求URL: {payment_url}?trade_no={trade_no}&agree=on")

            resp = self.session.get(
                payment_url,
                params=payment_params,
                headers=self._get_desktop_headers(referer=product_url),
                timeout=15
            )
            resp.raise_for_status()

            self.log(f"步骤5响应状态码: {resp.status_code}")
            self.log(f"步骤5响应体(前500字符): {resp.text[:500]}")

            # 解析支付宝表单
            soup = BeautifulSoup(resp.text, "html.parser")
            alipay_form = soup.find("form", id="alipaysubmit")
            if not alipay_form:
                alipay_form = soup.find("form")

            if not alipay_form:
                raise Exception("未找到支付宝表单")

            alipay_action = alipay_form.get("action", "")
            self.log(f"支付宝表单action: {alipay_action}")

            form_data = {}
            for input_tag in alipay_form.find_all("input", type="hidden"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    form_data[name] = value
                    self.log(f"  表单字段 {name}={value[:100]}...")

            if not alipay_action:
                raise Exception("支付宝表单action为空")

            # 步骤6: POST到支付宝网关
            self.log("=" * 80)
            self.log("【千寻寄售-下单】步骤6: POST到支付宝网关")
            self.log(f"请求URL: {alipay_action}")
            self.log(f"表单字段数: {len(form_data)}")

            resp = self.session.post(
                alipay_action,
                data=form_data,
                headers={
                    **self._get_desktop_headers(referer=self.BASE_URL + "/", content_type="application/x-www-form-urlencoded"),
                    "Origin": self.BASE_URL,
                },
                timeout=15,
                allow_redirects=False
            )

            self.log(f"步骤6响应状态码: {resp.status_code}")
            self.log(f"步骤6响应头: {dict(resp.headers)}")

            # 支付宝返回302重定向
            location = resp.headers.get("Location", "")
            if not location:
                raise Exception(f"支付宝网关未返回重定向，状态码: {resp.status_code}")

            self.log(f"步骤6重定向地址: {location}")

            # 步骤7: GET支付宝mclient链接，获取最终支付页面
            self.log("=" * 80)
            self.log("【千寻寄售-下单】步骤7: 获取最终支付页面")
            self.log(f"请求URL: {location}")

            resp = self.session.get(
                location,
                headers=self._get_desktop_headers(referer=self.BASE_URL + "/"),
                timeout=15,
                allow_redirects=False
            )

            self.log(f"步骤7响应状态码: {resp.status_code}")
            final_location = resp.headers.get("Location", "")

            if not final_location:
                raise Exception(f"支付宝未返回最终重定向，状态码: {resp.status_code}")

            self.log(f"步骤7最终支付地址: {final_location}")

            # 步骤8: 生成二维码
            from app.utils.qr_generator import generate_qr_base64
            qr_base64 = generate_qr_base64(final_location)
            self.log(f"二维码生成成功, trade_no={trade_no}")

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
        """登录千寻寄售平台"""
        try:
            # 步骤0: 先访问登录页面，获取初始session cookie
            login_page_url = f"{self.BASE_URL}/merchant/login"
            self.log("=" * 80)
            self.log("【千寻寄售-登录】步骤0：访问登录页面获取初始Cookie")
            self.log(f"请求URL: {login_page_url}")
            self.log(f"请求方法: GET")
            self.log("=" * 80)

            resp = self.session.get(login_page_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            }, timeout=15)

            self.log("=" * 80)
            self.log("【千寻寄售-登录】步骤0：登录页面响应")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"当前Cookies: {dict(self.session.cookies)}")
            self.log("=" * 80)

            # 真实接口路径为 /merchantapi/auth/login（全小写）
            login_url = f"{self.BASE_URL}/merchantapi/auth/login"
            login_data = {
                "username": username,
                "password": password
            }

            self.log("=" * 80)
            self.log("【千寻寄售-登录】步骤1：提交登录请求")
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
                "Referer": f"{self.BASE_URL}/merchant/login",
            }

            resp = self.session.post(login_url, json=login_data, headers=headers, timeout=15)

            self.log("=" * 80)
            self.log("【千寻寄售-登录】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text}")
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"登录失败: {result.get('msg', '未知错误')}")

            # 千寻寄售 token 在 JSON body 的 data.token 中（JWT）
            token = result.get("data", {}).get("token")

            if not token:
                raise Exception("登录成功但未获取到 token")

            self.merchant_token = token
            self.log(f"登录成功, token={token[:50]}...")

            # 保存 token 到 cookie（供 load_cookies/save_cookies 机制管理）
            self.session.cookies.set("merchant-token", token, domain="www.qianxun1688.com")

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

            # 真实接口路径为 /merchantapi/cash/index，使用 Authorization: Bearer token
            balance_url = f"{self.BASE_URL}/merchantapi/cash/index"

            self.log("=" * 80)
            self.log("【千寻寄售-查询余额】请求信息")
            self.log(f"请求URL: {balance_url}")
            self.log(f"请求方法: POST")
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
                "Referer": f"{self.BASE_URL}/merchant/cash",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Authorization": f"Bearer {self.merchant_token}",
            }

            resp = self.session.post(balance_url, json={"page": 1, "limit": 10}, headers=headers, timeout=15)

            self.log("=" * 80)
            self.log("【千寻寄售-查询余额】响应信息")
            self.log(f"响应状态码: {resp.status_code}")
            self.log(f"响应体: {resp.text}")
            self.log("=" * 80)

            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"查询余额失败: {result.get('msg', '未知错误')}")

            data = result.get("data", {})
            # 真实响应中 money 字段即为可用余额，没有不可用余额字段
            available_money = data.get("money", "0.000")
            try:
                available_money = float(available_money)
            except (ValueError, TypeError):
                available_money = 0.0

            self.log(f"查询余额成功: 可用余额={available_money}")

            return {
                "success": True,
                "message": "查询成功",
                "withdrawable": f"{available_money:.2f}",
                "non_withdrawable": "0.00"
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
                self.log(f"传入的是goods_key({goods_id})，通过消费者端接口查询数字ID...")

                # 保存商户token，避免被消费者端请求清除
                saved_token = self.merchant_token
                product_url = f"{self.BASE_URL}/details/{goods_id}"
                try:
                    info = self._fetch_goods_core(product_url)
                    numeric_id = info.get("goodid")
                except Exception as e:
                    self.log(f"消费者端查询失败: {e}")
                    raise Exception(f"无法获取goods_key={goods_id}对应的数字ID: {e}")
                finally:
                    # 恢复商户token到cookie
                    if saved_token:
                        self.session.cookies.set("merchant-token", saved_token, domain="www.qianxun1688.com")
                        self.merchant_token = saved_token

                if not numeric_id:
                    raise Exception(f"未找到goods_key={goods_id}对应的数字ID")
                self.log(f"找到商品 {goods_id} 对应的数字ID: {numeric_id}")
            else:
                numeric_id = int(goods_id)

            # 步骤1: 获取商品编辑信息（真实接口 /merchantapi/goods/get_edit）
            info_url = f"{self.BASE_URL}/merchantapi/goods/get_edit"
            info_data = {"id": str(numeric_id)}

            self.log("=" * 80)
            self.log("【千寻寄售-修改价格】步骤1：获取商品信息")
            self.log(f"请求URL: {info_url}")
            self.log(f"请求体: {json.dumps(info_data)}")
            self.log("=" * 80)

            headers = self._get_merchant_headers()
            resp = self.session.post(info_url, json=info_data, headers=headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()

            self.log(f"步骤1响应: {json.dumps(result, ensure_ascii=False)[:1500]}")

            if result.get("code") != 1:
                raise Exception(f"获取商品信息失败: {result.get('msg', '未知错误')}")

            goods = result.get("data", {}).get("goods", {})
            if not goods:
                raise Exception("获取商品信息成功但 data.goods 为空")

            # 步骤2: 提交价格修改（真实接口 /merchantapi/goods/edit，multipart/form-data）
            update_url = f"{self.BASE_URL}/merchantapi/goods/edit"

            # 从 goods 对象中提取需要提交的字段，构建 multipart/form-data
            form_fields = {
                "cate_id": goods.get("cate_id", ""),
                "name": goods.get("name", ""),
                "price": str(new_price),
                "cost_price": goods.get("cost_price", "0"),
                "theme": goods.get("theme", "default"),
                "limit_quantity": goods.get("limit_quantity", 1),
                "max_quantity": goods.get("max_quantity", 0),
                "sort": goods.get("sort", 0),
                "inventory_notify": goods.get("inventory_notify", 0),
                "content": goods.get("content", "<p><br></p>"),
                "remark": goods.get("remark", ""),
                "can_proxy": goods.get("can_proxy", 0),
                "distrib_rate": goods.get("distrib_rate", "0"),
                "wholesale_discount": goods.get("wholesale_discount", 0),
                "send_gift": goods.get("send_gift", 0),
                "card_order": goods.get("card_order", 0),
                "selectcard_fee": goods.get("selectcard_fee", "0"),
                "coupon_type": goods.get("coupon_type", 0),
                "inventory_notify_type": goods.get("inventory_notify_type", 1),
                "sold_notify": goods.get("sold_notify", 1),
                "contact_limit": goods.get("contact_limit", "default"),
                "id": str(numeric_id),
            }

            self.log("=" * 80)
            self.log("【千寻寄售-修改价格】步骤2：提交价格修改")
            self.log(f"请求URL: {update_url}")
            self.log(f"price={new_price}")
            self.log("=" * 80)

            # multipart/form-data 请求，不手动设置 Content-Type，让 requests 自动处理 boundary
            edit_headers = dict(headers)
            edit_headers.pop("Content-Type", None)

            resp = self.session.post(update_url, data=form_fields, headers=edit_headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()

            self.log(f"步骤2响应: {json.dumps(result, ensure_ascii=False)}")

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

            # 真实接口: POST /merchantapi/order/index
            orders_url = f"{self.BASE_URL}/merchantapi/order/index"

            # 固定查询已支付订单，status 为字符串 "1"
            query_data = {
                "page": 1,
                "limit": 10,
                "status": "1"
            }

            self.log("=" * 80)
            self.log("【千寻寄售-查询订单】请求信息")
            self.log(f"请求URL: {orders_url}")
            self.log(f"请求体: {json.dumps(query_data)}")
            self.log("=" * 80)

            headers = self._get_merchant_headers()
            resp = self.session.post(orders_url, json=query_data, headers=headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()

            self.log(f"查询订单响应: {json.dumps(result, ensure_ascii=False)[:1500]}")

            if result.get("code") != 1:
                raise Exception(f"查询订单失败: {result.get('msg', '未知错误')}")

            data = result.get("data", {})
            total = data.get("total", 0)
            orders_list = data.get("list", [])

            self.log(f"查询成功，共获取到 {len(orders_list)} 个订单（总计: {total}）")

            orders = []
            for order in orders_list:
                # status: 0-待处理/未支付, 1-已支付, 2-已发货/已完成 等
                status_val = order.get("status", 0)
                status_map = {0: "待付款", 1: "已支付", 2: "已完成", 3: "已取消"}
                status_text = status_map.get(status_val, f"未知({status_val})")

                # paytype: 2=支付宝, 3=微信
                paytype_val = order.get("paytype", 0)
                payment_method = "支付宝" if paytype_val == 2 else ("微信支付" if paytype_val == 3 else "未知")

                # 金额直接是字符串，无需除100
                total_price = order.get("total_price", "0.00")
                actual_price = order.get("finally_money", total_price)

                # 时间戳转换
                create_at = order.get("create_at", 0)
                if isinstance(create_at, (int, float)) and create_at > 0:
                    from datetime import datetime
                    trade_time = datetime.fromtimestamp(create_at).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    trade_time = ""

                orders.append({
                    "order_no": order.get("trade_no", ""),
                    "order_type": "普通订单",
                    "product_name": order.get("goods_name", ""),
                    "supplier": "",
                    "payment_method": payment_method,
                    "total_price": str(total_price),
                    "actual_price": str(actual_price),
                    "buyer_info": order.get("contact", "-"),
                    "status": status_text,
                    "card_status": "已取" if order.get("cards_count", 0) > 0 else "未取",
                    "card_password": order.get("take_card_password", ""),
                    "trade_time": trade_time,
                    "order_id": str(order.get("id", "")),
                })

            self.log(f"订单转换完成，共 {len(orders)} 条")

            return {
                "success": True,
                "message": "查询成功",
                "orders": orders,
                "total": total,
            }

        except Exception as e:
            self.log(f"查询订单失败: {str(e)}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "orders": [],
                "total": 0
            }
