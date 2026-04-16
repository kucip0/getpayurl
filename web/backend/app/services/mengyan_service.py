import json
import random
import re
import uuid
from typing import Tuple, Optional
from collections import OrderedDict
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.html_parser import unescape_html


class MengyanService(BaseService):
    """梦言云卡服务"""

    PLATFORM_CODE = "mengyan"
    BASE_URL = "https://www.np4.cn"
    TRACKING_COOKIE = "s0680c9c1"
    FINGERPRINT_ENABLED = True

    def login(self, username: str, password: str) -> dict:
        """登录梦言云卡店铺"""
        try:
            # 1. 访问主页
            resp = self.session.get(f"{self.BASE_URL}/")
            resp.raise_for_status()

            # 2. 访问登录页提取token
            resp = self.session.get(f"{self.BASE_URL}/login")
            resp.raise_for_status()
            html = unescape_html(resp.text)

            from app.utils.html_parser import extract_token_from_html
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

            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                raise Exception("登录失败: merchant Cookie不存在")

            self.log("登录成功")
            return {"success": True, "message": "登录成功", "shop_name": username}

        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise

    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格"""
        try:
            # 四云需要临时修改Accept头避免JSON编码
            original_accept = self.session.headers.get("Accept")
            self.session.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

            resp = self.session.get(product_url)
            resp.raise_for_status()

            # 恢复Accept头
            if original_accept:
                self.session.headers["Accept"] = original_accept

            # 处理转义的HTML（与原项目一致）
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

            # 提取价格（从 span.card__detail_price，与原项目一致）
            price_span = soup.find("span", class_="card__detail_price")
            if not price_span:
                raise Exception("未找到商品价格")
            
            # 提取价格文本（如 "￥50.00"），去除￥符号
            price_text = price_span.get_text().strip()
            original_price = float(price_text.replace("￥", "").replace("¥", ""))

            # 提取库存（从 span.card__detail_stock）
            stock = 0
            stock_span = soup.find("span", class_="card__detail_stock")
            if stock_span:
                stock_text = stock_span.get_text().strip()
                # 尝试提取数字
                import re
                stock_match = re.search(r'(\d+)', stock_text)
                if stock_match:
                    stock = int(stock_match.group(1))
                elif "少量" in stock_text or "充足" in stock_text:
                    stock = 999  # 库存少量或充足时设置为一个较大的值

            # 提取商品名称（从商品卡片的h3标签）
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
        """提交订单（包含步骤2.5和3.5）"""
        self.logs = []

        try:
            # 清除从数据库加载的Cookie（避免干扰步骤1）
            self.session.cookies.clear()
            self.log("步骤1前: 已清除从数据库加载的旧Cookie")

            # 步骤1
            cookie, params = self._step1_get_cookie_and_params(product_url)

            paymoney = round(float(new_price) * 1 * (1 + 0.05), 2)
            params["price"] = str(new_price)
            params["paymoney"] = str(paymoney)

            # 步骤2
            trade_no = self._step2_submit_order(cookie, params, product_url)

            # 步骤2.5: 指纹验证（四云特有）
            self._step25_check_buyer(trade_no)

            # 步骤3: 获取支付宝表单或重定向地址
            step3_result = self._step3_get_alipay_form(cookie, trade_no)

            # 步骤3.5: 如果是重定向地址，请求获取支付宝表单
            if isinstance(step3_result, str):
                # 四云发卡：步骤3返回的是重定向URL
                self.log("步骤3.5: 请求重定向地址，获取支付宝表单...")
                alipay_params = self._step35_get_alipay_form_from_redirect(step3_result, cookie)
            else:
                # 猴发卡：步骤3直接返回表单
                alipay_params = step3_result

            # 步骤4
            location1, alipay_cookies = self._step4_request_alipay_gateway(alipay_params)

            # 步骤5
            final_url = self._step5_follow_redirect(location1, alipay_cookies)

            # 步骤6
            qr_base64 = self._step6_generate_qrcode(final_url)

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

        # 解析URL
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path

        # 清除session中所有旧Cookie（确保服务器返回新的Set-Cookie）
        self.session.cookies.clear()
        self.log("DEBUG1-STEP1: 请求商品页面之前，已清除所有Cookie")

        # 请求商品页面（使用完整的浏览器请求头，与原始项目一致）
        request_url = f"{base_url}{path}"
        self.log(f"DEBUG1-STEP1: 请求URL={request_url}")
        
        # 临时覆盖session的Accept和Upgrade-Insecure-Requests（不修改session本身）
        step1_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Upgrade-Insecure-Requests": "1",
        }
        
        resp = self.session.get(request_url, headers=step1_headers, timeout=15)
        
        self.log(f"DEBUG1-STEP1: 响应状态码={resp.status_code}")
        self.log(f"DEBUG1-STEP1: response cookies={dict(resp.cookies)}")
        
        if resp.status_code != 200:
            raise Exception(f"步骤1请求失败: HTTP {resp.status_code}")

        # 处理转义的HTML（与get_product_price方法一致）
        html = resp.text.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')

        # 输出完整HTML响应到文件供调试
        import os
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, 'step1_response.html')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html)
        self.log(f"DEBUG1-STEP1: 完整HTML已保存到 {debug_file}")
        self.log(f"DEBUG1-STEP1: HTML前1000字符={html[:1000]}")

        # 调试日志：响应Cookie
        self.log(f"DEBUG1: response cookies={dict(resp.cookies)}")
        set_cookie_header = resp.headers.get('set-cookie', '')
        self.log(f"DEBUG1: Set-Cookie header (first 200 chars)={set_cookie_header[:200]}")

        # 提取 s0680c9c1 cookie
        cookie_value = None
        for cookie_name, cookie_val in resp.cookies.items():
            if "s0680c9c1" in cookie_name.lower():
                cookie_value = cookie_val
                break

        if not cookie_value:
            # 尝试从 set-cookie 头中直接提取
            set_cookies = resp.headers.get("set-cookie", "")
            match = re.search(r's0680c9c1=([^;]+)', set_cookies, re.IGNORECASE)
            if match:
                cookie_value = match.group(1)
            else:
                raise Exception("步骤1: 未找到 s0680c9c1 Cookie")

        # 清除session中所有Cookie，只设置s0680c9c1（与原始项目一致）
        self.session.cookies.clear()
        self.session.cookies.set("s0680c9c1", cookie_value)
        self.log(f"步骤1: 清除多余Cookie，只保留 s0680c9c1={cookie_value[:10]}...")
        self.log(f"DEBUG1: session cookies count={len(self.session.cookies)}")

        # DEBUG: log html length
        html_preview = html[:200].encode('ascii', 'ignore').decode('ascii')
        self.log(f"DEBUG1: html_len={len(html)}, preview={html_preview}")
        
        # 解析 HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # DEBUG: find all input tags
        all_inputs = soup.find_all("input")
        self.log(f"DEBUG1: found {len(all_inputs)} input tags")
        for i, inp in enumerate(all_inputs[:5]):
            name = inp.get("name", "")
            value = str(inp.get("value", ""))[:30].encode('ascii', 'ignore').decode('ascii')
            if name:
                self.log(f"DEBUG1: input[{i}] name={name}, value={value}")

        # 提取隐藏字段（与原始项目完全一致，逐个提取）
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

        # 与原始项目完全一致的参数结构
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
        return cookie_value, params

    def _step2_submit_order(self, cookie: str, params: dict, product_url: str) -> str:
        """步骤2: 提交订单（与原始项目完全一致）"""
        from urllib.parse import urlparse

        contact = f"1{random.randint(3,9)}{''.join([str(random.randint(0,9)) for _ in range(9)])}"

        # 计算 paymoney: price * quantity * (1 + fee_rate)
        quantity = 1
        price_val = float(params["price"]) if params["price"] else float(params["danjia"])
        fee_rate_val = float(params["fee_rate"])
        paymoney = round(price_val * quantity * (1 + fee_rate_val), 2)

        # 解析URL获取base_url
        parsed = urlparse(product_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 与原始项目完全一致的请求体（使用[]直接访问，不用.get()）
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
            "pid": params.get("pid", "47"),  # 梦言云卡使用params中的pid，默认47（支付宝）
        }

        # 完整浏览器请求头（与原始项目完全一致）
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
            "Sec-Fetch-Dest": "iframe",  # 梦言云卡使用iframe
            "Referer": product_url,  # 使用实际的商品URL作为Referer
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        # 梦言云卡需要从商品页面获取默认的pid
        # 如果params中没有pid，使用47（支付宝）
        if "pid" not in params or not params["pid"]:
            params["pid"] = "47"  # 梦言云卡默认支付宝

        # 输出完整的请求调试信息
        request_url = f"{base_url}/pay/order"
        self.log(f"DEBUG 2 (request): URL={request_url}")
        self.log(f"DEBUG 2 (request): 完整请求体={order_data}")
        self.log(f"DEBUG 2 (request): Referer={headers['Referer']}")
        self.log(f"DEBUG 2 (request): Origin={headers['Origin']}")
        self.log(f"DEBUG 2 (request): Sec-Fetch-Dest={headers['Sec-Fetch-Dest']}")

        # 调试日志 - 请求前Cookie状态
        cookie_before = [(c.name, c.value[:10], c.domain, c.path) for c in self.session.cookies]
        self.log(f"DEBUG 2 (pre-request): cookies={cookie_before}")

        resp = self.session.post(
            f"{base_url}/pay/order",
            data=order_data,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        
        # 调试日志 - 输出完整Cookie信息
        cookie_details = [(c.name, c.value[:10], c.domain, c.path) for c in self.session.cookies]
        self.log(f"DEBUG 2: status={resp.status_code}")
        self.log(f"DEBUG 2: cookies={cookie_details}")
        self.log(f"DEBUG 2: content-type={resp.headers.get('content-type', '')}")
        self.log(f"DEBUG 2: resp.text前100字符={resp.text[:100]}")

        # 处理转义的HTML
        # 如果响应被引号包裹，说明是JSON编码的字符串，需要先解码
        import html as html_module
        raw_text = resp.text
        
        # 检查是否被引号包裹（JSON字符串格式）
        if raw_text.startswith('"') and raw_text.endswith('"'):
            self.log("DEBUG 2: 检测到JSON编码的HTML字符串，进行解码")
            try:
                import json
                raw_text = json.loads(resp.text)
            except:
                self.log("DEBUG 2: JSON解码失败，使用原始文本")
        
        # 处理HTML实体转义
        step2_html = html_module.unescape(raw_text)
        # 处理JSON风格的转义符
        step2_html = step2_html.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        
        # 保存调试HTML到文件
        import os
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, 'step2_response.html')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(step2_html)
        self.log(f"DEBUG 2: 完整HTML已保存到 {debug_file}")
        
        soup = BeautifulSoup(step2_html, "html.parser")

        trade_no_input = soup.find("input", {"name": "trade_no"})
        if not trade_no_input or not trade_no_input.get("value"):
            # 调试日志：输出响应摘要
            self.log(f"DEBUG 2: 页面中没有trade_no字段")
            self.log(f"DEBUG 2: 原始响应前200字符={resp.text[:200]}")
            self.log(f"DEBUG 2: 处理后HTML前200字符={step2_html[:200]}")
            
            # 检查是否是错误页面
            if "没有可用的支付渠道" in step2_html:
                raise Exception("步骤2: 订单提交失败，该商品没有可用的支付渠道")
            elif "库存" in step2_html:
                raise Exception("步骤2: 订单提交失败，商品库存不足")
            
            # 尝试从页面文本中提取（备用方案）
            match = re.search(r'trade_no["\s:=]+([\w]+)', resp.text)
            if match:
                trade_no = match.group(1)
                self.log("步骤2: 提交订单成功（从文本提取）")
                return trade_no
            raise Exception(
                f"步骤2: 未找到 trade_no，可能库存不足或需要验证码。\n"
                f"响应摘要: {resp.text[:200]}"
            )

        trade_no = trade_no_input.get("value")
        self.log(f"DEBUG 2: trade_no={trade_no}")
        self.log("步骤2: 提交订单成功")
        return trade_no

    def _step25_check_buyer(self, orderid: str):
        """步骤2.5: 验证设备指纹（与原始项目完全一致）"""
        # 生成新的设备指纹（模拟浏览器的guid()函数，与原始项目一致）
        fingerprint = str(uuid.uuid4())
        self.log(f"生成新的设备指纹: {fingerprint[:10]}...")
        
        # wxauth为空字符串（与原始项目一致）
        wxauth = ""

        check_data = {
            "trade_no": orderid,
            "fingerprint": fingerprint,
            "wxauth": wxauth,
        }
        
        # 调试日志
        self.log(f"DEBUG 2.5: trade_no={orderid}, fingerprint={fingerprint[:10]}...")
        self.log(f"DEBUG 2.5: URL={self.BASE_URL}/index/pay/check_buyer")

        resp = self.session.post(
            f"{self.BASE_URL}/index/pay/check_buyer",
            data=check_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "sec-ch-ua-platform": '"Windows"',
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
                "sec-ch-ua-mobile": "?0",
                "Origin": self.BASE_URL,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": f"{self.BASE_URL}/pay/order",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Priority": "u=0, i"
            },
            timeout=15
        )
        
        # 调试日志
        self.log(f"DEBUG 2.5: 响应状态码={resp.status_code}")
        self.log(f"DEBUG 2.5: 响应体={resp.text[:300]}")
        
        resp.raise_for_status()
        
        try:
            result = resp.json()
            status = result.get("status", "")
            msg = result.get("msg", "")
            
            self.log(f"DEBUG 2.5: status={status}, msg={msg}")
            
            if status == "tip":
                raise Exception(f"指纹验证失败: {msg}")
            elif status == "collect":
                self.log("步骤2.5: 需要关注公众号，尝试继续...")
            else:
                self.log("步骤2.5: 指纹验证通过")
        except Exception as e:
            if "指纹验证" in str(e):
                raise
            self.log("步骤2.5: 响应非JSON格式")

    def _step3_get_alipay_form(self, cookie: str, orderid: str) -> str:
        """步骤3: 获取重定向地址"""
        # 拼接完整的URL（包含查询参数）
        full_url = f"{self.BASE_URL}/index/pay/payment?trade_no={orderid}&agree=on"
        
        # 完整浏览器请求头（与原始项目一致）
        headers = {
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
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

        resp = self.session.get(
            full_url,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )

        # 处理 302 重定向
        if resp.status_code in (302, 301):
            location = resp.headers.get("Location")
            if not location:
                raise Exception("步骤3: 响应头中无 Location 字段")
            self.log(f"步骤3 重定向地址: {location}")
            return location
        
        if resp.status_code != 200:
            raise Exception(f"步骤3请求失败: HTTP {resp.status_code}")

        # 如果不是重定向，尝试直接解析表单（兼容猴发卡）
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form", {"id": "alipaysubmit"})
        if not form:
            raise Exception(f"步骤3: 未找到支付宝表单。\n响应体: {resp.text[:200]}")

        self.log("步骤3: 获取支付宝表单成功")
        return {"direct_form": True}

    def _step35_get_alipay_form_from_redirect(self, redirect_url: str, cookie: str) -> dict:
        """步骤3.5: 请求重定向地址获取支付宝表单（四云发卡专用）"""
        self.log(f"步骤3.5 URL: {redirect_url}")
        
        # 完整浏览器请求头
        headers = {
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/index/pay/payment",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        resp = self.session.get(
            redirect_url,
            headers=headers,
            timeout=15
        )
        
        if resp.status_code != 200:
            raise Exception(f"步骤3.5请求失败: HTTP {resp.status_code}")
        
        # 解析 HTML，查找支付宝表单 form#alipaysubmit
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form", {"id": "alipaysubmit"})
        if not form:
            raise Exception(f"步骤3.5: 未找到支付宝表单。\n响应体: {resp.text[:200]}")
        
        # 提取表单参数
        alipay_params = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value")
            if name and value is not None:
                alipay_params[name] = value
        
        if not alipay_params:
            raise Exception("步骤3.5: 支付宝表单参数为空")
        
        self.log("步骤3.5: 获取支付宝表单成功")
        return alipay_params

    def _step4_request_alipay_gateway(self, alipay_params: dict) -> Tuple[str, dict]:
        """步骤4: 请求支付宝网关，获取第一次重定向地址"""
        gateway_url = "https://openapi.alipay.com/gateway.do?charset=utf-8"

        # 按真实请求顺序重组参数（使用OrderedDict）
        ordered_params = OrderedDict()
        param_order = [
            "app_id", "method", "format", "return_url", "charset",
            "sign_type", "timestamp", "version", "notify_url",
            "biz_content", "sign",
        ]
        for key in param_order:
            if key in alipay_params:
                ordered_params[key] = alipay_params[key]
        
        # 追加剩余未知参数
        for key, val in alipay_params.items():
            if key not in ordered_params:
                ordered_params[key] = val

        # 固定参数覆盖
        ordered_params["method"] = "alipay.trade.wap.pay"
        ordered_params["charset"] = "utf-8"

        # 四云特有的notify_url
        ordered_params["notify_url"] = "http://not.pay.4yun.4yuns.com/pay/Alipay_Wap/notify"

        # 修改 biz_content 中的 product_code
        if "biz_content" in ordered_params:
            try:
                biz = json.loads(ordered_params["biz_content"])
            except (json.JSONDecodeError, TypeError):
                biz = {}
            biz["product_code"] = "QUICK_WAP_WAY"
            ordered_params["biz_content"] = json.dumps(biz, separators=(",", ":"), ensure_ascii=True)

        # URL 编码参数
        encoded_data = urlencode(ordered_params)

        # 完整浏览器请求头
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": self.BASE_URL,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.BASE_URL}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self.log(f"步骤4请求体: {encoded_data[:100]}...")

        resp = self.session.post(
            gateway_url,
            data=encoded_data,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )

        if resp.status_code not in (302, 301):
            raise Exception(
                f"步骤4: 预期302重定向，实际HTTP {resp.status_code}\n"
                f"响应摘要: {resp.text[:200]}"
            )

        location = resp.headers.get("Location")
        if not location:
            raise Exception("步骤4: 响应头中无Location字段")

        alipay_cookies = dict(resp.cookies)
        self.log("步骤4: 请求支付宝网关成功")
        return location, alipay_cookies

    def _step5_follow_redirect(self, location: str, alipay_cookies: dict) -> str:
        """步骤5: 跟随重定向"""
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

        self.log("步骤5: 跟随重定向成功")
        return final_url

    def _step6_generate_qrcode(self, url: str) -> str:
        """步骤6: 生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("步骤6: 生成二维码成功")
        return qr_base64

    def query_orders(
        self,
        status: int = 1,
        start_date: str = "",
        end_date: str = "",
        pay_type: Optional[int] = None,
        order_type: Optional[int] = None
    ) -> dict:
        """查询订单列表（梦言云卡）"""
        try:
            # 1. 检查登录态
            if not self.load_cookies():
                return {
                    "success": False,
                    "message": "店铺未登录，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            # 验证merchant Cookie是否存在
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            # 2. 构建查询URL
            base_url = f"{self.BASE_URL}/merchant/order/index.html"
            params = {"status": status}

            if start_date and end_date:
                params["date_range"] = f"{start_date} - {end_date}"

            if pay_type is not None:
                params["paytype"] = pay_type

            if order_type is not None:
                params["order_type"] = order_type

            # 3. 请求订单列表页面
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

            # 4. 处理转义的HTML
            html = unescape_html(resp.text)

            # 保存调试HTML到文件
            import os
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, 'mengyan_orders_debug.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)

            # 5. 检测是否跳转到登录页
            # 更准确的检测：检查是否真的没有订单表格且有登录表单
            has_order_table = '<table class="table mb-0">' in html or '订单列表' in html
            has_login_form = 'action="/index/user/doLogin"' in html or 'login' in html.lower()

            if not has_order_table and has_login_form:
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "orders": [],
                    "total": 0
                }

            # 6. 解析订单表格
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
        """查询账户余额（梦言云卡）"""
        try:
            # 1. 检查登录态
            if not self.load_cookies():
                return {
                    "success": False,
                    "message": "店铺未登录，请在平台管理中重新登录",
                    "withdrawable": "0.000",
                    "non_withdrawable": "0.000"
                }

            # 验证merchant Cookie是否存在
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                return {
                    "success": False,
                    "message": "店铺登录已过期，请在平台管理中重新登录",
                    "withdrawable": "0.000",
                    "non_withdrawable": "0.000"
                }

            # 2. 请求提现页面
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

            # 3. 处理转义的HTML
            html = unescape_html(resp.text)
            soup = BeautifulSoup(html, "html.parser")

            # 4. 解析可提现金额
            withdrawable = "0.000"
            non_withdrawable = "0.000"

            # 方法1: 查找包含"可提现金额"的label，然后找到对应的input value
            labels = soup.find_all("label", class_="col-md-2 col-form-label")
            for label in labels:
                if "可提现金额" in label.get_text():
                    # 找到包含该label的form-group
                    form_group = label.find_parent("div", class_="form-group row")
                    if form_group:
                        # 查找该form-group中的input
                        input_elem = form_group.find("input", type="text")
                        if input_elem and input_elem.get("value"):
                            withdrawable = input_elem["value"].strip()
                            break

            # 方法2: 查找不可提现金额（text-danger span）
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
