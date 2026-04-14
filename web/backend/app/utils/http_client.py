import os
from typing import Dict, Optional, Tuple

import requests


def create_session(verify_ssl: bool = False) -> requests.Session:
    """创建HTTP会话，配置浏览器伪装"""
    session = requests.Session()

    # 禁用SSL验证
    if not verify_ssl:
        session.verify = False
        # 清除所有SSL相关环境变量，避免干扰
        for env_var in ['REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSLKEYLOGFILE']:
            if env_var in os.environ:
                del os.environ[env_var]

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


def extract_cookie_from_response(
    response: requests.Response,
    cookie_name: str
) -> Optional[str]:
    """从响应中提取指定Cookie值"""
    return response.cookies.get(cookie_name)
