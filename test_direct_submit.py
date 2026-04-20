import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
from urllib.parse import urlencode
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
})

# 获取CSRF Token
resp = session.get("https://www.xinfaka.com/single/8BF70AA3E39D", verify=False)
csrf_match = __import__('re').search(r'name="csrf-token"\s+content="([^"]+)"', resp.text)
csrf_token = csrf_match.group(1)

soup = BeautifulSoup(resp.text, "html.parser")
goods_id = soup.find("input", {"id": "GoodsId"}).get("value")
shop_id = soup.find("input", {"id": "shopId"}).get("value")

# 创建订单
order_data = {
    "GoodsId": goods_id,
    "quantity": "1",
    "shopId": shop_id,
    "is_sms": "0",
    "sms_receive": "",
    "take_card_password": "",
    "payId": "18",
    "payType": "1",
    "coupon": "",
    "is_xh": "0",
    "kami_id": "",
    "is_dk": "0",
    "visit_password": "",
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-CSRF-TOKEN": csrf_token,
    "X-Requested-With": "XMLHttpRequest",
}

resp = session.post("https://www.xinfaka.com/goods/createorder", data=order_data, headers=headers, verify=False)
result = resp.json()
print(f"订单响应: {result}")

data = result.get("data", {})
order_url = data.get("url", "") if isinstance(data, dict) else ""
if not order_url:
    print("订单创建失败")
    sys.exit(1)

order_no = order_url.split("/")[-1]
print(f"订单号: {order_no}")

# 访问支付页面
pay_url = f"https://www.xinfaka.com/payment/{order_no}"
resp1 = session.get(pay_url, allow_redirects=False, verify=False)
url2 = resp1.headers.get("Location")

resp2 = session.get(url2, allow_redirects=False, verify=False)
url3 = resp2.headers.get("Location")

resp3 = session.get(url3, verify=False)

# 提取支付宝表单
soup = BeautifulSoup(resp3.text, "html.parser")
form = soup.find("form", {"id": "alipaysubmit"})

alipay_params = {}
for inp in form.find_all("input", {"type": "hidden"}):
    name = inp.get("name")
    value = inp.get("value")
    if name and value is not None:
        alipay_params[name] = value

print(f"\n提取到 {len(alipay_params)} 个参数:")
for k, v in alipay_params.items():
    print(f"  {k}: {v[:60]}..." if len(str(v)) > 60 else f"  {k}: {v}")

# 方法1: 不修改参数,直接提交
print("\n方法1: 直接提交原始表单参数...")
gateway_url = "https://openapi.alipay.com/gateway.do?charset=utf-8"

submit_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.yiyipay.com",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.yiyipay.com/",
}

encoded_data = urlencode(alipay_params)
print(f"请求数据长度: {len(encoded_data)}")

resp4 = session.post(
    gateway_url,
    data=encoded_data,
    headers=submit_headers,
    allow_redirects=False,
    verify=False
)

print(f"响应状态码: {resp4.status_code}")
if resp4.status_code in [301, 302]:
    print(f"重定向到: {resp4.headers.get('Location', '')[:100]}")
else:
    print(f"响应内容: {resp4.text[:300]}")
