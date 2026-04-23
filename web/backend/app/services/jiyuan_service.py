import html as html_module
import json
import random
import re
from collections import OrderedDict
from typing import Tuple
from urllib.parse import urlencode, quote_plus

import requests
from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.html_parser import unescape_html, extract_token_from_html, parse_form_data


class JiyuanService(BaseService):
    """纪元发卡服务"""

    PLATFORM_CODE = "jiyuan"
    BASE_URL = "https://buy.jiyuanfaka.com"
    TRACKING_COOKIE = "s61ba3b56"

    def login(self, username: str, password: str, verify_code: str = "", csrf_token: str = "") -> dict:
        """登录纪元发卡店铺"""
        try:
            # 1. 访问主页获取初始Cookie
            resp = self.session.get(f"{self.BASE_URL}/")
            resp.raise_for_status()

            # 2. 访问登录页提取token
            resp = self.session.get(f"{self.BASE_URL}/login")
            resp.raise_for_status()
            html = unescape_html(resp.text)

            token = extract_token_from_html(html)
            if not token:
                raise Exception("无法提取CSRF Token")

            # 3. POST登录
            login_data = {
                "__token__": token,
                "username": username,
                "password": password,
                "rememberme": "1",
            }

            resp = self.session.post(
                f"{self.BASE_URL}/index/user/doLogin",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 1:
                raise Exception(f"登录失败: {result.get('msg', '未知错误')}")

            # 4. 验证merchant Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                raise Exception("登录失败: merchant Cookie不存在")

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
        """获取商品价格"""
        try:
            # 使用merchant_session（已登录）获取商品页面
            resp = self.session.get(product_url)
            resp.raise_for_status()

            self.log(f"DEBUG: 获取商品页面成功，HTML长度: {len(resp.text)}")

            # 处理转义的HTML（与原项目一致）
            html = resp.text.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
            
            soup = BeautifulSoup(html, "html.parser")

            # 调试：检查是否找到关键元素
            price_span = soup.find("span", class_="card__detail_price")
            self.log(f"DEBUG: price_span found: {price_span is not None}")
            
            goods_box = soup.find("div", class_="goods_box")
            self.log(f"DEBUG: goods_box found: {goods_box is not None}")

            # 提取商品参数（从隐藏input）
            params = {}
            for input_elem in soup.find_all("input", attrs={"name": True}):
                name = input_elem["name"]
                value = input_elem.get("value", "")
                params[name] = value

            # 提取商品ID
            goodid = params.get("goodid")
            if not goodid:
                raise Exception("未找到商品ID")

            # 提取价格（从 span.card__detail_price，与原项目一致）
            if not price_span:
                raise Exception("未找到商品价格")
            
            # 提取价格文本（如 "￥50.00"），去除￥符号
            price_text = price_span.get_text().strip()
            self.log(f"DEBUG: price_text: {price_text}")
            original_price = float(price_text.replace("￥", "").replace("¥", ""))

            # 提取库存（从 span.card__detail_stock）
            stock = 0
            stock_span = soup.find("span", class_="card__detail_stock")
            if stock_span:
                stock_text = stock_span.get_text().strip()
                # 尝试提取数字
                stock_match = re.search(r'(\d+)', stock_text)
                if stock_match:
                    stock = int(stock_match.group(1))
                elif "少量" in stock_text or "充足" in stock_text:
                    stock = 999  # 库存少量或充足时设置为一个较大的值

            # 提取商品名称（从商品卡片的h3标签）
            product_name = "未知商品"
            if goods_box:
                h3_tag = goods_box.find("h3")
                if h3_tag:
                    product_name = h3_tag.get_text().strip()

            # 填充默认值
            params.setdefault("feePayer", "1")
            params.setdefault("fee_rate", "0.035")
            params.setdefault("min_fee", "0.3")
            params.setdefault("rate", "100")
            params.setdefault("is_contact_limit", "default")
            params.setdefault("limit_quantity", "1")
            params.setdefault("cardNoLength", "0")
            params.setdefault("cardPwdLength", "0")
            params.setdefault("is_discount", "0")
            params.setdefault("coupon_ctype", "0")
            params.setdefault("coupon_value", "0")
            params.setdefault("sms_price", "0")

            return {
                "success": True,
                "product_id": goodid,
                "product_name": product_name,
                "original_price": original_price,
                "stock": stock,
            }

        except Exception as e:
            self.log(f"获取商品价格失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def modify_goods_price(self, goods_id: str, new_price: str) -> dict:
        """修改商品价格"""
        try:
            # 步骤1: 获取商品编辑数据
            self.log("正在获取商品信息...")
            goods_data = self._get_goods_edit_data(goods_id)
            
            # 步骤2: 提交价格修改
            self.log(f"正在修改价格为 ¥{new_price}...")
            result = self._submit_goods_price_modify(goods_id, new_price, goods_data)
            
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

    def _get_goods_edit_data(self, goods_id: str) -> dict:
        """获取商品编辑页面的表单数据"""
        edit_url = f"{self.BASE_URL}/merchant/goods/edit.html"
        
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/merchant/goods/index.html",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        resp = self.session.get(
            edit_url,
            params={"id": goods_id},
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        # 处理转义的HTML
        html_content = resp.text
        html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        
        html_content = html_module.unescape(html_content)
        html_content = html_content.replace('&#x20;', ' ')
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 查找表单
        form = soup.find("form", {"id": "goods-form"})
        if not form:
            form = soup.find("form", {"id": "form1"})
        if not form:
            form = soup.find("form")
        
        if not form:
            raise Exception("商品编辑页面中未找到表单")
        
        # 提取所有 input 字段
        goods_data = {}
        for inp in form.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            
            input_type = inp.get("type", "text")
            
            # 处理 radio 和 checkbox（只提取选中的）
            if input_type in ("radio", "checkbox"):
                if inp.get("checked"):
                    goods_data[name] = inp.get("value", "1")
            # 其他 input 类型（text, hidden, number 等）
            else:
                value = inp.get("value")
                if value is not None:
                    goods_data[name] = value
        
        # 提取 textarea 字段
        for textarea in form.find_all("textarea"):
            name = textarea.get("name")
            if not name:
                continue
            
            # Summernote 富文本编辑器
            if textarea.get("class") and "d-none" in textarea.get("class", []):
                summernote_div = soup.find("div", {"id": f"summernote-{name}"})
                if summernote_div:
                    goods_data[name] = str(summernote_div.decode_contents())
            else:
                value = textarea.get_text()
                if value is not None:
                    goods_data[name] = value
        
        # 提取 select 字段
        for select in form.find_all("select"):
            name = select.get("name")
            if not name:
                continue
            selected_option = select.find("option", selected=True)
            if selected_option and selected_option.get("value"):
                goods_data[name] = selected_option.get("value")
            else:
                first_option = select.find("option")
                if first_option and first_option.get("value"):
                    goods_data[name] = first_option.get("value")
        
        if not goods_data:
            raise Exception("商品编辑页面表单数据为空")
        
        return goods_data

    def _submit_goods_price_modify(self, goods_id: str, new_price: str, goods_data: dict) -> dict:
        """提交商品价格修改"""
        edit_url = f"{self.BASE_URL}/merchant/goods/edit.html"
        
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/merchant/goods/edit.html?id={goods_id}",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=1, i",
        }
        
        # 使用前置数据，仅覆盖价格
        form_data = goods_data.copy()
        form_data["id"] = str(goods_id)
        form_data["price"] = str(new_price)
        
        resp = self.session.post(
            edit_url,
            data=form_data,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        # 解析响应
        result = resp.json()
        
        if result.get("code") != 1:
            error_msg = result.get("msg", "修改商品价格失败，未知错误")
            raise Exception(f"修改商品价格失败: {error_msg}")
        
        return result

    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单并生成支付二维码"""
        self.logs = []

        try:
            # 步骤1: 获取Cookie和参数
            cookie, params = self._step1_get_cookie_and_params(product_url)

            # 设置价格（纪元发卡paymoney直接等于price）
            params["price"] = str(new_price)
            params["paymoney"] = str(new_price)
            params["danjia"] = str(new_price)

            # 步骤2: 提交订单
            trade_no = self._step2_submit_order(cookie, params)

            # 步骤3: 获取易支付表单
            yipay_params = self._step3_get_yipay_form(trade_no)

            # 步骤4: POST到易支付网关
            redirect_path = self._step4_post_yipay(yipay_params)

            # 步骤5: GET二维码页面
            code_url = self._step5_get_qrcode_page(redirect_path)

            # 步骤6: GET submitwap页面获取支付宝表单
            alipay_params = self._step6_get_alipay_form(code_url)

            # 步骤7: POST到支付宝网关
            location = self._step7_post_alipay_gateway(alipay_params)

            # 步骤8: 跟随重定向获取最终支付URL
            final_url = self._step8_follow_redirect(location)

            # 生成二维码
            qr_base64 = self._step9_generate_qrcode(final_url)

            return {
                "success": True,
                "order_id": trade_no,
                "qr_code_base64": qr_base64,
                "payment_url": final_url,
                "logs": self.logs,
            }

        except Exception as e:
            self.log(f"订单处理失败: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "logs": self.logs,
            }

    def _step1_get_cookie_and_params(self, url: str) -> Tuple[str, dict]:
        """步骤1: 获取Cookie和商品参数"""
        # 先访问首页获取初始Cookie
        self.session.get(f"{self.BASE_URL}/", headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"
        })

        # 获取商品页面（移动端UA）
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        self.log(f"DEBUG: GET {url}")
        resp = self.session.get(url, headers=headers)
        self.log(f"DEBUG: 响应状态码: {resp.status_code}")
        self.log(f"DEBUG: 响应长度: {len(resp.text)}")
        resp.raise_for_status()

        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")

        # 提取Cookie
        cookie = self.session.cookies.get(self.TRACKING_COOKIE)
        if not cookie:
            cookie = resp.cookies.get(self.TRACKING_COOKIE)
        self.log(f"DEBUG: TRACKING_COOKIE存在: {bool(cookie)}")

        # 提取参数
        params = {}
        for input_elem in soup.find_all("input", attrs={"name": True}):
            name = input_elem["name"]
            value = input_elem.get("value", "")
            params[name] = value
        self.log(f"DEBUG: 提取到参数: {list(params.keys())}")

        # 从支付方式区域提取 pid（支付宝）
        if not params.get("pid"):
            for pay_box in soup.find_all("div", class_="pay_box"):
                pay_text = pay_box.get_text()
                if "支付宝" in pay_text or "zfb" in str(pay_box).lower():
                    data_pid = pay_box.get("data-pid")
                    if data_pid:
                        params["pid"] = data_pid
                        break
            self.log(f"DEBUG: 从页面提取pid: {params.get('pid')}")

        # 如果 kucun 为 0 或空，尝试从商品备注提取库存数字
        if params.get("kucun") in ("0", "", "0.00"):
            remark_div = soup.find("div", class_="goods_remark")
            if remark_div:
                remark_text = remark_div.get_text().strip()
                match = re.search(r'(\d+)', remark_text)
                if match:
                    params["kucun"] = match.group(1)
                else:
                    price_div = soup.find("div", class_="goods_price")
                    if price_div:
                        params["kucun"] = price_div.get_text().strip()
            self.log(f"DEBUG: 修正后kucun: {params.get('kucun')}")

        # 填充默认值（纪元发卡）
        defaults = {
            "feePayer": "1", "fee_rate": "0.035", "min_fee": "0.3",
            "rate": "100", "is_contact_limit": "default",
            "limit_quantity": "1", "cardNoLength": "0",
            "cardPwdLength": "0", "is_discount": "0",
            "coupon_ctype": "0", "coupon_value": "0",
            "sms_price": "0", "is_pwdforsearch": "",
            "is_coupon": "", "select_cards": ""
        }
        for key, value in defaults.items():
            params.setdefault(key, value)

        self.log("步骤1: 获取Cookie和商品参数成功")
        return cookie, params

    def _step2_submit_order(self, cookie: str, params: dict) -> str:
        """步骤2: 提交订单"""
        # 生成随机手机号
        contact = f"1{random.randint(3,9)}{''.join([str(random.randint(0,9)) for _ in range(9)])}"

        order_data = {
            "goodid": params.get("goodid"),
            "cateid": params.get("cateid"),
            "quantity": "1",
            "contact": contact,
            "email": "",
            "couponcode": "",
            "pwdforsearch1": "",
            "pwdforsearch2": "",
            "is_contact_limit": params.get("is_contact_limit"),
            "limit_quantity": params.get("limit_quantity"),
            "userid": params.get("userid"),
            "token": params.get("token"),
            "cardNoLength": params.get("cardNoLength"),
            "cardPwdLength": params.get("cardPwdLength"),
            "is_discount": params.get("is_discount"),
            "coupon_ctype": params.get("coupon_ctype"),
            "coupon_value": params.get("coupon_value"),
            "sms_price": params.get("sms_price"),
            "paymoney": params.get("paymoney"),
            "danjia": params.get("danjia"),
            "is_pwdforsearch": params.get("is_pwdforsearch"),
            "is_coupon": params.get("is_coupon"),
            "price": params.get("price"),
            "kucun": params.get("kucun"),
            "select_cards": params.get("select_cards"),
            "feePayer": params.get("feePayer"),
            "fee_rate": params.get("fee_rate"),
            "min_fee": params.get("min_fee"),
            "rate": params.get("rate"),
            "pid": params.get("pid"),
        }

        headers = {
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": self.BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/details/{params.get('goodid')}",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self.log(f"DEBUG: POST {self.BASE_URL}/pay/order")
        self.log(f"DEBUG: 请求参数: {order_data}")
        resp = self.session.post(
            f"{self.BASE_URL}/pay/order",
            data=order_data,
            headers=headers,
        )
        self.log(f"DEBUG: 响应状态码: {resp.status_code}")
        self.log(f"DEBUG: 响应长度: {len(resp.text)}")
        resp.raise_for_status()

        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")

        trade_no_input = soup.find("input", attrs={"name": "trade_no"})
        if not trade_no_input or not trade_no_input.get("value"):
            self.log(f"DEBUG: 响应内容前500字: {resp.text[:500]}")
            raise Exception("未找到trade_no")

        trade_no = trade_no_input["value"]
        self.log(f"DEBUG: trade_no: {trade_no}")
        self.log("步骤2: 提交订单成功")
        return trade_no

    def _step3_get_yipay_form(self, trade_no: str) -> dict:
        """步骤3: 获取易支付表单参数"""
        headers = {
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/pay/order",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self.log(f"DEBUG: GET {self.BASE_URL}/index/pay/payment?trade_no={trade_no}&agree=on")
        resp = self.session.get(
            f"{self.BASE_URL}/index/pay/payment",
            params={"trade_no": trade_no, "agree": "on"},
            headers=headers,
        )
        self.log(f"DEBUG: 响应状态码: {resp.status_code}")
        self.log(f"DEBUG: 响应长度: {len(resp.text)}")
        resp.raise_for_status()

        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")

        # 查找易支付表单
        form = soup.find("form", attrs={"action": "https://pay.jiyuanfaka.com/submit.php"})
        if not form:
            form = soup.find("form", action=re.compile(r"submit\.php"))
        if not form:
            self.log(f"DEBUG: 响应内容前500字: {resp.text[:500]}")
            raise Exception("未找到易支付表单")

        yipay_params = {}
        for input_elem in form.find_all("input", attrs={"type": "hidden"}):
            name = input_elem.get("name")
            value = input_elem.get("value", "")
            if name:
                yipay_params[name] = value

        if not yipay_params:
            raise Exception("未解析到易支付参数")

        self.log(f"DEBUG: 易支付参数: {yipay_params}")
        self.log("步骤3: 获取易支付表单成功")
        return yipay_params

    def _step4_post_yipay(self, yipay_params: dict) -> str:
        """步骤4: POST到易支付网关，获取跳转路径"""
        submit_url = "https://pay.jiyuanfaka.com/submit.php"
        headers = {
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": self.BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self.log(f"DEBUG: POST {submit_url}")
        self.log(f"DEBUG: 请求参数: {yipay_params}")
        resp = self.session.post(
            submit_url,
            data=yipay_params,
            headers=headers,
        )
        self.log(f"DEBUG: 响应状态码: {resp.status_code}")
        self.log(f"DEBUG: 响应长度: {len(resp.text)}")
        resp.raise_for_status()

        # 解析JS跳转到二维码页面
        html = resp.text
        match = re.search(r"window\.location\.replace\(['\"](.+?)['\"]\)", html)
        if not match:
            match = re.search(r"window\.location\.href\s*=\s*['\"](.+?)['\"]", html)
        if not match:
            self.log(f"DEBUG: 响应内容前500字: {resp.text[:500]}")
            raise Exception("步骤4: 未找到支付跳转地址")

        redirect_path = match.group(1)
        self.log(f"DEBUG: 跳转路径: {redirect_path}")
        self.log("步骤4: POST易支付网关成功")
        return redirect_path

    def _step5_get_qrcode_page(self, redirect_path: str) -> str:
        """步骤5: GET二维码页面，提取code_url"""
        if redirect_path.startswith("http"):
            qrcode_url = redirect_path
        else:
            qrcode_url = f"https://pay.jiyuanfaka.com{redirect_path}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": "https://pay.jiyuanfaka.com/submit.php",
        }

        self.log("=" * 80)
        self.log("步骤5 请求详情")
        self.log("=" * 80)
        self.log(f"请求URL: GET {qrcode_url}")
        self.log(f"请求头: {json.dumps(dict(headers), ensure_ascii=False, indent=2)}")
        self.log("-" * 80)

        resp = self.session.get(qrcode_url, headers=headers)

        self.log("-" * 80)
        self.log("步骤5 响应详情")
        self.log("-" * 80)
        self.log(f"响应状态码: {resp.status_code}")
        self.log(f"响应头: {json.dumps(dict(resp.headers), ensure_ascii=False, indent=2)}")
        self.log(f"响应体长度: {len(resp.text)}")
        self.log(f"响应体(完整未截断):\n{resp.text}")
        self.log("=" * 80)
        resp.raise_for_status()

        code_match = re.search(r"var\s+code_url\s*=\s*['\"](.+?)['\"]", resp.text)
        if not code_match:
            raise Exception("步骤5: 未找到支付二维码URL")

        code_url = code_match.group(1)
        self.log(f"DEBUG: code_url: {code_url}")
        self.log("步骤5: 获取二维码页面成功")
        return code_url

    def _step6_get_alipay_form(self, code_url: str) -> dict:
        """步骤6: GET submitwap页面，提取支付宝表单参数"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": "https://pay.jiyuanfaka.com/",
        }

        self.log("=" * 80)
        self.log("步骤6 请求详情")
        self.log("=" * 80)
        self.log(f"请求URL: GET {code_url}")
        self.log(f"请求头: {json.dumps(dict(headers), ensure_ascii=False, indent=2)}")
        self.log("-" * 80)

        resp = self.session.get(code_url, headers=headers)

        self.log("-" * 80)
        self.log("步骤6 响应详情")
        self.log("-" * 80)
        self.log(f"响应状态码: {resp.status_code}")
        self.log(f"响应头: {json.dumps(dict(resp.headers), ensure_ascii=False, indent=2)}")
        self.log(f"响应体长度: {len(resp.text)}")
        self.log(f"响应体(完整未截断):\n{resp.text}")
        self.log("=" * 80)
        resp.raise_for_status()

        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")

        form = soup.find("form", id="alipaysubmit")
        if not form:
            raise Exception("步骤6: 未找到支付宝表单")

        alipay_params = {}
        for input_elem in form.find_all("input", attrs={"type": "hidden"}):
            name = input_elem.get("name")
            value = input_elem.get("value")
            if name and value is not None:
                # 关键修复：解码HTML实体（如 &lbrace; &rcub; &lowbar; &colon; 等）
                decoded_value = html_module.unescape(value)
                alipay_params[name] = decoded_value

        if not alipay_params:
            raise Exception("步骤6: 未解析到支付宝参数")

        self.log(f"DEBUG: 支付宝表单参数keys: {list(alipay_params.keys())}")
        if "biz_content" in alipay_params:
            self.log(f"DEBUG: biz_content前200字: {alipay_params['biz_content'][:200]}")
        self.log("步骤6: 获取支付宝表单成功")
        return alipay_params

    def _step7_post_alipay_gateway(self, alipay_params: dict) -> str:
        """步骤7: POST到支付宝网关，获取Location"""
        gateway_url = "https://openapi.alipay.com/gateway.do"

        # 严格按照真实请求的参数顺序构建
        ordered_params = OrderedDict()
        param_order = [
            "app_id", "version", "alipay_sdk", "charset", "format",
            "sign_type", "method", "timestamp", "notify_url",
            "return_url", "biz_content", "sign",
        ]
        for key in param_order:
            if key in alipay_params:
                ordered_params[key] = alipay_params[key]
        # 剩余参数（如果有）
        for key, val in alipay_params.items():
            if key not in ordered_params:
                ordered_params[key] = val

        # 不修改任何参数，保持原始值（charset保持UTF-8大写，biz_content包含product_code）
        # method 已在前面的param_order中设置为 alipay.trade.wap.pay

        # 使用 quote_plus 使空格编码为 +（而非 urlencode 默认的 %20）
        encoded_data = urlencode(ordered_params, quote_via=quote_plus)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": "https://pay.jiyuanfaka.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://pay.jiyuanfaka.com/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self.log("=" * 80)
        self.log("步骤7 请求详情")
        self.log("=" * 80)
        self.log(f"请求URL: POST {gateway_url}")
        self.log(f"请求头: {json.dumps(dict(headers), ensure_ascii=False, indent=2)}")
        self.log(f"请求体(完整未截断): {encoded_data}")
        if "biz_content" in ordered_params:
            self.log(f"biz_content(完整未截断): {ordered_params['biz_content']}")
        self.log("-" * 80)

        resp = self.session.post(
            gateway_url,
            data=encoded_data,
            headers=headers,
            timeout=15,
            allow_redirects=False,
        )

        self.log("-" * 80)
        self.log("步骤7 响应详情")
        self.log("-" * 80)
        self.log(f"响应状态码: {resp.status_code}")
        self.log(f"响应头: {json.dumps(dict(resp.headers), ensure_ascii=False, indent=2)}")
        self.log(f"响应体长度: {len(resp.text)}")
        self.log(f"响应体(完整未截断):\n{resp.text}")
        self.log("=" * 80)

        if resp.status_code not in (302, 301):
            raise Exception(f"步骤7: 预期302重定向，实际HTTP {resp.status_code}")

        location = resp.headers.get("Location")
        if not location:
            raise Exception("步骤7: 响应头中无Location字段")

        self.log(f"DEBUG: Location: {location}")
        self.log("步骤7: POST支付宝网关成功")
        return location

    def _step8_follow_redirect(self, location: str) -> str:
        """步骤8: 跟随重定向获取最终支付URL"""
        alipay_cookies = dict(self.session.cookies)

        self.log("=" * 80)
        self.log("步骤8 请求详情")
        self.log("=" * 80)
        self.log(f"请求URL: GET {location}")
        self.log(f"请求Cookie: {json.dumps(alipay_cookies, ensure_ascii=False, indent=2)}")
        self.log("-" * 80)

        resp = self.session.get(
            location,
            cookies=alipay_cookies,
            allow_redirects=False,
        )

        self.log("-" * 80)
        self.log("步骤8 响应详情")
        self.log("-" * 80)
        self.log(f"响应状态码: {resp.status_code}")
        self.log(f"响应头: {json.dumps(dict(resp.headers), ensure_ascii=False, indent=2)}")
        self.log(f"响应体长度: {len(resp.text)}")
        self.log(f"响应体(完整未截断):\n{resp.text}")
        self.log("=" * 80)

        if resp.status_code in (301, 302):
            final_url = resp.headers.get("Location", resp.url)
        else:
            final_url = resp.url

        self.log(f"DEBUG: 最终支付URL: {final_url}")
        self.log("步骤8: 获取最终支付URL成功")
        return final_url

    def _step9_generate_qrcode(self, url: str) -> str:
        """生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("生成二维码成功")
        return qr_base64

    def query_orders(
        self,
        status: int = 1,
        start_date: str = "",
        end_date: str = "",
        pay_type: int = None,
        order_type: int = None
    ) -> dict:
        """查询订单列表"""
        try:
            # 1. 检查登录态
            self.log("DEBUG: 开始加载Cookies...")
            cookies_loaded = self.load_cookies()
            self.log(f"DEBUG: Cookies加载结果: {cookies_loaded}")
            
            if not cookies_loaded:
                return {
                    "success": False,
                    "message": "未登录，请先在平台管理中登录店铺",
                    "orders": [],
                    "total": 0
                }
            
            # 检查merchant Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            self.log(f"DEBUG: merchant Cookie存在: {bool(merchant_cookie)}")
            if merchant_cookie:
                self.log(f"DEBUG: merchant Cookie值: {merchant_cookie[:30]}...")
            else:
                self.log("DEBUG: merchant Cookie值为空!")
            
            if not merchant_cookie:
                return {
                    "success": False,
                    "message": "店铺登录信息丢失，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }
            
            # 2. 构建查询URL
            params = {
                "paytype": pay_type if pay_type is not None else "",
                "status": status,
                "cid": "0",
                "order_type": order_type if order_type is not None else "",
                "type": "0",
                "keywords": "",
                "has_send": "",
            }
            
            # 添加日期范围
            if start_date and end_date:
                params["date_range"] = f"{start_date} - {end_date}"
            else:
                params["date_range"] = "0"
            
            query_string = urlencode(params)
            url = f"{self.BASE_URL}/merchant/order/index.html?{query_string}"
            
            self.log(f"查询订单: {url}")
            
            # 调试：检查Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            self.log(f"DEBUG: merchant Cookie存在: {bool(merchant_cookie)}")
            self.log(f"DEBUG: 当前session cookies数量: {len(self.session.cookies)}")
            
            # 3. 发起请求
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
                "Host": "buy.jiyuanfaka.com",
                "Referer": f"{self.BASE_URL}/merchant/order/index.html",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            }
            
            resp = self.session.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            self.log(f"DEBUG: 响应状态码: {resp.status_code}")
            self.log(f"DEBUG: 响应长度: {len(resp.text)}")
            
            # 调试：更准确地检测登录页面
            # 检查是否被重定向到登录页（查看是否有订单表格）
            has_order_table = '<table class="table mb-0">' in resp.text or '订单列表' in resp.text
            has_login_form = 'action="/index/user/doLogin"' in resp.text
            
            if not has_order_table and has_login_form:
                self.log("WARNING: 检测到登录表单且无订单表格，Cookie可能已过期")
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }
            
            # 4. 处理HTML（处理转义字符）
            html_content = unescape_html(resp.text)
            self.log(f"DEBUG: 处理后HTML长度: {len(html_content)}")
            
            # 5. 解析订单
            from app.utils.html_parser import parse_order_table
            orders = parse_order_table(html_content)
            
            self.log(f"查询到 {len(orders)} 个订单")
            
            # 调试：保存HTML用于检查
            if len(orders) == 0:
                # 替换日期中的/为-，避免路径错误
                safe_start = start_date.replace('/', '-') if start_date else 'none'
                safe_end = end_date.replace('/', '-') if end_date else 'none'
                debug_file = f"debug_orders_{status}_{safe_start}_{safe_end}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.log(f"DEBUG: 已保存HTML到 {debug_file}")
            
            # 6. 返回结果
            return {
                "success": True,
                "message": "查询成功",
                "orders": orders,
                "total": len(orders)
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
        """查询账户余额"""
        try:
            # 1. 检查登录态
            self.log("DEBUG: 开始查询余额...")
            cookies_loaded = self.load_cookies()
            self.log(f"DEBUG: Cookies加载结果: {cookies_loaded}")
            
            if not cookies_loaded:
                return {
                    "success": False,
                    "message": "未登录，请先在平台管理中登录店铺",
                    "withdrawable": "0.000",
                    "non_withdrawable": "0.000"
                }
            
            # 检查merchant Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                return {
                    "success": False,
                    "message": "店铺登录信息丢失，请在平台管理中重新登录",
                    "withdrawable": "0.000",
                    "non_withdrawable": "0.000"
                }
            
            # 2. 请求提现页面（包含余额信息）
            url = f"{self.BASE_URL}/merchant/cash/apply.html"
            self.log(f"查询余额: {url}")
            
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Connection": "keep-alive",
                "Host": "buy.jiyuanfaka.com",
                "Referer": f"{self.BASE_URL}/merchant/index/index.html",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            }
            
            resp = self.session.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            self.log(f"DEBUG: 响应状态码: {resp.status_code}")
            self.log(f"DEBUG: 响应长度: {len(resp.text)}")
            
            # 3. 处理HTML
            html_content = unescape_html(resp.text)
            
            # 4. 解析余额信息
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 查找可提现金额
            withdrawable = "0.000"
            non_withdrawable = "0.000"
            
            # 方法1: 查找包含"可提现金额"的label，然后获取同级input的value
            labels = soup.find_all("label", class_="col-md-2 col-form-label")
            for label in labels:
                if "可提现金额" in label.get_text():
                    # 找到父级row
                    form_group = label.find_parent("div", class_="form-group row")
                    if form_group:
                        input_elem = form_group.find("input", type="text")
                        if input_elem and input_elem.get("value"):
                            withdrawable = input_elem["value"].strip()
                    break
            
            # 方法2: 查找不可提现金额（在text-danger span中）
            danger_span = soup.find("span", class_="text-danger")
            if danger_span:
                # 获取span的文本
                non_withdrawable = danger_span.get_text().strip()
            
            self.log(f"可提现金额: {withdrawable}")
            self.log(f"不可提现金额: {non_withdrawable}")
            
            # 5. 返回结果
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
                "withdrawable": "0.000",
                "non_withdrawable": "0.000"
            }
