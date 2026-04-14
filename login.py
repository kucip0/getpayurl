"""
登录模块 - 猴发卡网自动登录

功能:
    - 自动登录获取 Cookie
    - 提取 merchant Cookie 用于后续请求
    - 复用已登录会话

使用方法:
    from login import login_to_houfaka
    
    # 登录并获取会话
    session, cookies = login_to_houfaka(username, password)
"""

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import re
import warnings

# 禁用 SSL 验证警告
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def login_to_houfaka(username, password, base_url="https://www.houfaka.com"):
    """
    登录猴发卡网
    
    参数:
        username: 用户名
        password: 密码
        base_url: 网站基础 URL
    
    返回:
        tuple: (requests.Session, dict)
            - session: 已登录的会话对象（包含所有 Cookie）
            - cookies: 字典格式的所有 Cookie
    
    异常:
        Exception: 登录失败时抛出异常，包含错误信息
    """
    session = requests.Session()
    session.verify = False
    
    # 设置基础请求头
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
        "Referer": f"{base_url}/login",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Priority": "u=1, i",
    })
    
    # 首先访问主页获取初始 Cookie
    session.get(base_url, timeout=15)
    
    # 访问登录页面获取 __token__
    login_page_url = f"{base_url}/login"
    login_page_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": f"{base_url}/",
        "Priority": "u=0, i",
    }
    
    resp = session.get(login_page_url, headers=login_page_headers, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"访问登录页面失败: HTTP {resp.status_code}")
    
    # 处理可能被转义的响应内容
    html_content = resp.text
    # 反转义 HTML 内容（处理 \/ 和 \" 等转义）
    html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
    
    # 调试：检查是否被重定向到登录页
    if "login" in resp.url.lower() and "/login" not in login_page_url.lower():
        # 可能已经被重定向，检查页面内容
        pass
    
    # 从 HTML 中提取 __token__
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 方法1：查找所有 input 标签（包括自闭合）
    token_input = soup.find("input", {"name": "__token__"})
    if token_input and token_input.get("value"):
        token_value = token_input.get("value")
    else:
        # 方法2：正则提取（支持不同顺序的属性）
        match = re.search(r'<input[^>]*name=["\']__token__["\'][^>]*value=["\']([^"\']+)["\']', html_content)
        if not match:
            # 方法3：value 在 name 前面
            match = re.search(r'<input[^>]*value=["\']([^"\']+)["\'][^>]*name=["\']__token__["\']', html_content)
        if not match:
            # 方法4：宽松匹配（支持自闭合标签 />）
            match = re.search(r'name=["\']__token__["\'][^>]*value=["\']([^"\']+)["\']', html_content)
        if not match:
            # 方法5：查找所有隐藏 input
            for inp in soup.find_all("input", {"type": "hidden"}):
                if inp.get("name") == "__token__" and inp.get("value"):
                    token_value = inp.get("value")
                    break
            else:
                # 输出调试信息
                debug_info = f"登录页面URL: {resp.url}\n"
                debug_info += f"响应长度: {len(html_content)}\n"
                debug_info += f"完整响应内容:\n{html_content}\n"
                debug_info += f"响应头: {dict(resp.headers)}"
                raise Exception(f"登录页面中未找到 __token__ 参数\n{debug_info}")
        else:
            token_value = match.group(1)
    
    # 登录请求
    login_url = f"{base_url}/index/user/doLogin"
    
    # 构建请求体
    form_data = {
        "__token__": token_value,
        "username": username,
        "password": password,
        "rememberme": "1",
    }
    
    resp = session.post(
        login_url,
        data=form_data,
        timeout=15
    )
    
    if resp.status_code != 200:
        raise Exception(f"登录请求失败: HTTP {resp.status_code}")
    
    # 解析响应
    result = resp.json()
    
    if result.get("code") != 1:
        error_msg = result.get("msg", "登录失败，未知错误")
        raise Exception(f"登录失败: {error_msg}")
    
    # 登录成功，提取 merchant Cookie
    merchant_cookie = session.cookies.get("merchant")
    if not merchant_cookie:
        raise Exception("登录成功但未找到 merchant Cookie")
    
    # 返回会话和 Cookie 字典
    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
    
    return session, cookies_dict


if __name__ == "__main__":
    # 测试登录
    import json
    
    test_username = "yousha01"
    test_password = "Suorona258"
    
    try:
        session, cookies = login_to_houfaka(test_username, test_password)
        print("登录成功!")
        print(f"Merchant Cookie: {cookies.get('merchant', 'N/A')}")
        print(f"所有 Cookie: {json.dumps(cookies, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"登录失败: {e}")


def modify_goods_price(session, goods_id, new_price, goods_data, base_url="https://www.houfaka.com"):
    """
    修改商品价格
    
    参数:
        session: 已登录的 requests.Session 对象（自动管理 Cookie）
        goods_id: 商品 ID
        new_price: 新价格（字符串，如 "50.00"）
        goods_data: 商品完整数据字典（从前置请求获取的所有参数）
        base_url: 网站基础 URL
    
    返回:
        dict: 响应结果，包含 goods_id 等信息
    
    异常:
        Exception: 修改失败时抛出异常
    """
    edit_url = f"{base_url}/merchant/goods/edit.html"
    
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
        "Referer": f"{base_url}/merchant/goods/edit.html?id={goods_id}",
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
    
    resp = session.post(
        edit_url,
        data=form_data,
        headers=headers,
        timeout=15
    )
    
    if resp.status_code != 200:
        raise Exception(f"修改商品价格请求失败: HTTP {resp.status_code}")
    
    # 解析响应
    result = resp.json()
    
    if result.get("code") != 1:
        error_msg = result.get("msg", "修改商品价格失败，未知错误")
        raise Exception(f"修改商品价格失败: {error_msg}")
    
    return result


def get_goods_edit_data(session, goods_id, base_url="https://www.houfaka.com"):
    """
    获取商品编辑页面的表单数据（用于修改价格前的数据准备）
    
    参数:
        session: 已登录的 requests.Session 对象（自动管理 Cookie）
        goods_id: 商品 ID
        base_url: 网站基础 URL
    
    返回:
        dict: 商品表单数据字典（包含所有需要提交的参数）
    
    异常:
        Exception: 获取失败时抛出异常
    """
    edit_url = f"{base_url}/merchant/goods/edit.html"
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": f"{base_url}/merchant/goods/index.html",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Priority": "u=0, i",
    }
    
    resp = session.get(
        edit_url,
        params={"id": goods_id},
        headers=headers,
        timeout=15
    )
    
    if resp.status_code != 200:
        raise Exception(f"获取商品编辑页面失败: HTTP {resp.status_code}")
    
    # 处理可能被转义的响应内容
    html_content = resp.text
    # 反转义 HTML 内容
    import html as html_module
    html_content = html_module.unescape(html_content)
    html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
    html_content = html_content.replace('&#x20;', ' ')
    
    # 解析 HTML 提取表单数据
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 尝试查找表单（支持不同ID）
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
    
    # 提取 textarea 字段（如 remark）
    for textarea in form.find_all("textarea"):
        name = textarea.get("name")
        if not name:
            continue
        
        # Summernote 富文本编辑器：内容在 div#summernote-{name} 中
        if textarea.get("class") and "d-none" in textarea.get("class", []):
            summernote_div = soup.find("div", {"id": f"summernote-{name}"})
            if summernote_div:
                # 获取 HTML 内容
                goods_data[name] = str(summernote_div.decode_contents())
        else:
            # 普通 textarea
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
            # 如果没有 selected 属性，取第一个 option
            first_option = select.find("option")
            if first_option and first_option.get("value"):
                goods_data[name] = first_option.get("value")
    
    if not goods_data:
        raise Exception("商品编辑页面表单数据为空")
    
    return goods_data
