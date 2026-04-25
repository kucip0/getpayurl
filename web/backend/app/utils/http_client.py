import os
from typing import Dict, Optional, Tuple

import requests
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_session(verify_ssl: bool = False) -> requests.Session:
    """创建HTTP会话，配置浏览器伪装"""
    session = requests.Session()

    # 禁用SSL验证
    if not verify_ssl:
        session.verify = False
        # 不再删除SSL环境变量，只设置session.verify=False即可

    # 浏览器请求头（必须使用Windows User-Agent，否则获取不到正确的支付渠道）
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })

    return session


def create_fingerprint_session(verify_ssl: bool = False) -> "Session":
    """创建带TLS指纹的HTTP会话（用于四云发卡等需要浏览器TLS指纹的平台）
    
    使用curl_cffi库模拟Chrome浏览器的TLS握手，避免被服务器拒绝。
    这在Linux生产环境中尤为重要，因为默认的requests库使用OpenSSL，
    其TLS指纹与浏览器不同。
    """
    try:
        from curl_cffi import requests as curl_requests
        
        # 使用Chrome浏览器的TLS指纹（chrome124是最新的稳定版本）
        session = curl_requests.Session(
            impersonate="chrome124",
            verify=False
        )
        
        # 浏览器请求头
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        
        return session
    except ImportError:
        # 如果curl_cffi未安装，回退到普通session
        print("Warning: curl_cffi not installed, falling back to regular session")
        return create_session(verify_ssl=verify_ssl)


def extract_cookie_from_response(
    response: requests.Response,
    cookie_name: str
) -> Optional[str]:
    """从响应中提取指定Cookie值"""
    return response.cookies.get(cookie_name)
