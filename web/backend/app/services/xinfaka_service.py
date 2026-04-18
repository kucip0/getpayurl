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

    def login(self, username: str, password: str, verify_code: str = "") -> dict:
        """登录新发卡平台
        
        Args:
            username: 手机号
            password: 密码
            verify_code: 验证码（可选，如果不提供则尝试不带验证码的登录）
        """
        try:
            # 1. 访问登录页面获取 CSRF Token（如果还没有）
            if not hasattr(self, 'captcha_csrf_token') or not self.captcha_csrf_token:
                resp = self.session.get(f"{self.BASE_URL}/merchant/login")
                resp.raise_for_status()

                # 2. 从 meta 标签提取 CSRF Token
                html = resp.text
                match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
                if not match:
                    raise Exception("无法获取 CSRF Token")

                self.captcha_csrf_token = match.group(1)
                self.log("获取 CSRF Token 成功")
            
            csrf_token = self.captcha_csrf_token

            # 3. POST 登录
            login_data = {
                "mobile": username,
                "password": password,
            }
            
            # 如果提供了验证码，添加到请求中
            if verify_code:
                login_data["verify_code"] = verify_code
                self.log("使用验证码登录")
            else:
                self.log("警告：新发卡平台需要验证码，尝试不带验证码的登录")

            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/merchant/login",
            }

            resp = self.session.post(
                f"{self.BASE_URL}/merchant/login",
                data=login_data,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()

            # 调试日志
            self.log(f"登录响应: {result}")

            # 4. 检查响应
            if result.get("code") != 0:
                error_msg = result.get("msg", "登录失败")
                
                # 检查是否需要二级验证
                data = result.get("data", {})
                if isinstance(data, dict) and data.get("type") in [1, 2]:
                    login_type = data["type"]
                    type_name = "SMS" if login_type == 1 else "Email"
                    value = data.get("value", "")
                    raise Exception(f"需要{type_name}二级验证，验证账号: {value}")
                
                raise Exception(f"登录失败: {error_msg}")

            # 5. 验证 Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                # 新发卡可能使用不同的 Cookie 名称
                all_cookies = dict(self.session.cookies)
                if not all_cookies:
                    raise Exception("登录失败: 无 Cookie")
                self.log("登录成功（Cookie 检查通过）")
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
        """获取验证码图片（保持 session 一致性，用于后续登录）"""
        try:
            # 清除旧的 session，确保获取新的 CSRF Token
            self.session.cookies.clear()
            self.captcha_csrf_token = ""
            
            # 访问登录页面获取 CSRF Token 和 Session
            resp = self.session.get(f"{self.BASE_URL}/merchant/login")
            resp.raise_for_status()
            
            # 从 meta 标签提取 CSRF Token
            html = resp.text
            match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
            if match:
                self.captcha_csrf_token = match.group(1)
                self.log("获取 CSRF Token 成功")
            
            # 获取验证码图片（使用同一个 session）
            captcha_url = f"{self.BASE_URL}/captcha/merchantlogin?{random.random()}"
            resp = self.session.get(captcha_url, timeout=15)
            resp.raise_for_status()
            
            self.log(f"验证码图片获取成功，大小: {len(resp.content)} bytes")
            return resp.content
        except Exception as e:
            self.log(f"获取验证码失败: {str(e)}")
            raise

    def login_with_captcha_session(self, username: str, password: str, verify_code: str) -> dict:
        """使用已获取验证码的 session 登录（保持 session 一致性）
        
        这个方法必须在 get_captcha_image() 之后调用，使用同一个 session
        """
        # 直接使用已保存的 CSRF Token 和 session
        if not self.captcha_csrf_token:
            raise Exception("请先获取验证码")
        
        try:
            # POST 登录（使用同一个 session）
            login_data = {
                "mobile": username,
                "password": password,
                "verify_code": verify_code,
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": self.captcha_csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/merchant/login",
            }

            resp = self.session.post(
                f"{self.BASE_URL}/merchant/login",
                data=login_data,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            result = resp.json()

            # 调试日志
            self.log(f"登录响应: {result}")

            # 检查响应
            if result.get("code") != 0:
                error_msg = result.get("msg", "登录失败")
                
                # 检查是否需要二级验证
                data = result.get("data", {})
                if isinstance(data, dict) and data.get("type") in [1, 2]:
                    login_type = data["type"]
                    type_name = "SMS" if login_type == 1 else "Email"
                    value = data.get("value", "")
                    raise Exception(f"需要{type_name}二级验证，验证账号: {value}")
                
                raise Exception(f"登录失败: {error_msg}")

            # 验证 Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                all_cookies = dict(self.session.cookies)
                if not all_cookies:
                    raise Exception("登录失败: 无 Cookie")
                self.log("登录成功（Cookie 检查通过）")
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
        """获取商品价格"""
        try:
            resp = self.session.get(product_url)
            resp.raise_for_status()

            # 处理转义的HTML
            html = resp.text.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
            
            soup = BeautifulSoup(html, "html.parser")

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

            # 提取价格
            price_span = soup.find("span", class_="card__detail_price")
            if not price_span:
                raise Exception("未找到商品价格")
            
            price_text = price_span.get_text().strip()
            original_price = float(price_text.replace("￥", "").replace("¥", ""))

            # 提取库存
            stock = 0
            stock_span = soup.find("span", class_="card__detail_stock")
            if stock_span:
                stock_text = stock_span.get_text().strip()
                stock_match = re.search(r'(\d+)', stock_text)
                if stock_match:
                    stock = int(stock_match.group(1))
                elif "少量" in stock_text or "充足" in stock_text:
                    stock = 999

            # 提取商品名称
            product_name = "未知商品"
            goods_box = soup.find("div", class_="goods_box")
            if goods_box:
                h3_tag = goods_box.find("h3")
                if h3_tag:
                    product_name = h3_tag.get_text().strip()

            # 填充默认值
            params.setdefault("feePayer", "2")
            params.setdefault("fee_rate", "0.05")
            params.setdefault("min_fee", "0.1")
            params.setdefault("rate", "100")

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
        import html as html_module
        html_content = resp.text
        html_content = html_module.unescape(html_content)
        html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
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
            
            if input_type in ("radio", "checkbox"):
                if inp.get("checked"):
                    goods_data[name] = inp.get("value", "1")
            else:
                value = inp.get("value")
                if value is not None:
                    goods_data[name] = value
        
        # 提取 textarea 字段
        for textarea in form.find_all("textarea"):
            name = textarea.get("name")
            if not name:
                continue
            
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
        """提交订单"""
        self.logs = []

        try:
            # 清除从数据库加载的Cookie
            self.session.cookies.clear()
            self.log("步骤1前: 已清除从数据库加载的旧Cookie")

            # 步骤1: 获取Cookie及商品参数
            cookie, params = self._step1_get_cookie_and_params(product_url)

            # 计算价格
            paymoney = round(float(new_price) * 1 * (1 + 0.05), 2)
            params["price"] = str(new_price)
            params["paymoney"] = str(paymoney)

            # 步骤2: 提交订单
            trade_no = self._step2_submit_order(cookie, params, product_url)

            # 步骤3: 获取支付表单
            pay_params = self._step3_get_payment_form(cookie, trade_no)

            # 步骤4: 提交到支付网关
            pay_id = self._step4_submit_gateway(pay_params)

            # 步骤5: 获取支付宝表单
            alipay_params = self._step5_get_alipay_form(pay_id)

            # 步骤6: 请求支付宝网关
            location1, alipay_cookies = self._step6_request_alipay_gateway(alipay_params)

            # 步骤7: 跟随重定向
            final_url = self._step7_follow_redirect(location1, alipay_cookies)

            # 步骤8: 生成二维码
            qr_base64 = self._step8_generate_qrcode(final_url)

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
        """查询订单列表"""
        try:
            if not self.load_cookies():
                return {
                    "success": False,
                    "message": "店铺未登录，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            base_url = f"{self.BASE_URL}/merchant/order/index.html"
            params = {"status": status}

            if start_date and end_date:
                params["date_range"] = f"{start_date} - {end_date}"

            if pay_type is not None:
                params["paytype"] = pay_type

            if order_type is not None:
                params["order_type"] = order_type

            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": f"{self.BASE_URL}/merchant/order/index.html?status={status}",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Priority": "u=0, i",
            }

            resp = self.session.get(
                base_url,
                params=params,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()

            html = unescape_html(resp.text)

            has_order_table = '<table class="table mb-0">' in html or '订单列表' in html
            has_login_form = 'action="/index/user/doLogin"' in html or 'login' in html.lower()

            if not has_order_table and has_login_form:
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            from app.utils.html_parser import parse_order_table
            orders = parse_order_table(html)

            self.log(f"查询成功，共获取到 {len(orders)} 个订单")

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
            if not self.load_cookies():
                return {
                    "success": False,
                    "message": "店铺未登录，请在平台管理中重新登录",
                    "withdrawable": "0.000",
                    "non_withdrawable": "0.000"
                }

            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "withdrawable": "0.000",
                    "non_withdrawable": "0.000"
                }

            cash_url = f"{self.BASE_URL}/merchant/cash/apply.html"
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": f"{self.BASE_URL}/merchant/index/index.html",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Priority": "u=0, i",
            }

            resp = self.session.get(cash_url, headers=headers, timeout=15)
            resp.raise_for_status()

            html = unescape_html(resp.text)
            soup = BeautifulSoup(html, "html.parser")

            withdrawable = "0.000"
            non_withdrawable = "0.000"

            labels = soup.find_all("label", class_="col-md-2 col-form-label")
            for label in labels:
                if "可提现金额" in label.get_text():
                    form_group = label.find_parent("div", class_="form-group row")
                    if form_group:
                        input_elem = form_group.find("input", type="text")
                        if input_elem and input_elem.get("value"):
                            withdrawable = input_elem["value"].strip()
                            break

            danger_span = soup.find("span", class_="text-danger")
            if danger_span:
                non_withdrawable = danger_span.get_text().strip()

            self.log(f"查询余额成功: 可提现={withdrawable}, 不可提现={non_withdrawable}")

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
