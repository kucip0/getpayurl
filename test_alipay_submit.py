import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
from urllib.parse import urlencode
import json

# 模拟完整的流程
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
})

# 步骤1: 访问商品页面获取CSRF Token
print("步骤1: 访问商品页面...")
resp = session.get("https://www.xinfaka.com/single/8BF70AA3E39D", verify=False)
csrf_match = __import__('re').search(r'name="csrf-token"\s+content="([^"]+)"', resp.text)
csrf_token = csrf_match.group(1) if csrf_match else ""
print(f"CSRF Token: {csrf_token[:20]}...")

# 步骤2: 提取商品信息
soup = BeautifulSoup(resp.text, "html.parser")
goods_id = soup.find("input", {"id": "GoodsId"}).get("value")
shop_id = soup.find("input", {"id": "shopId"}).get("value")
print(f"商品ID: {goods_id}, shopId: {shop_id[:20]}...")

# 步骤3: 创建订单
print("\n步骤2: 创建订单...")
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
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "https://www.xinfaka.com",
    "Referer": "https://www.xinfaka.com/single/8BF70AA3E39D",
}

resp = session.post(
    "https://www.xinfaka.com/goods/createorder",
    data=order_data,
    headers=headers,
    verify=False
)
result = resp.json()
print(f"订单创建响应: {result}")

data = result.get("data", {})
if isinstance(data, list) and data:
    order_url = data[0].get("url", "")
elif isinstance(data, dict):
    order_url = data.get("url", "")
    
order_no = order_url.split("/")[-1]
print(f"订单号: {order_no}")

# 步骤4: 访问支付页面
print("\n步骤3: 访问支付页面...")
pay_url = f"https://www.xinfaka.com/payment/{order_no}"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "X-CSRF-TOKEN": csrf_token,
    "Referer": "https://www.xinfaka.com/",
}

resp1 = session.get(pay_url, headers=headers, timeout=15, allow_redirects=False, verify=False)
print(f"/payment 状态码: {resp1.status_code}")
url2 = resp1.headers.get("Location")
print(f"重定向1: {url2}")

resp2 = session.get(url2, headers=headers, timeout=15, allow_redirects=False, verify=False)
print(f"/disburse 状态码: {resp2.status_code}")
url3 = resp2.headers.get("Location")
print(f"重定向2: {url3}")

resp3 = session.get(url3, headers=headers, timeout=15, verify=False)
print(f"yiypipay 状态码: {resp3.status_code}")

# 提取支付宝表单
soup = BeautifulSoup(resp3.text, "html.parser")
form = soup.find("form", {"id": "alipaysubmit"})
if form:
    print("\n找到支付宝表单!")
    alipay_params = {}
    for inp in form.find_all("input", {"type": "hidden"}):
        name = inp.get("name")
        value = inp.get("value")
        if name and value is not None:
            alipay_params[name] = value
    
    print(f"提取到 {len(alipay_params)} 个参数:")
    for k, v in alipay_params.items():
        print(f"  {k}: {v[:50]}..." if len(str(v)) > 50 else f"  {k}: {v}")
    
    # 提交到支付宝网关
    print("\n步骤4: 提交到支付宝网关...")
    gateway_url = "https://openapi.alipay.com/gateway.do?charset=utf-8"
    
    ordered_params = OrderedDict()
    param_order = [
        "app_id", "method", "format", "return_url", "charset",
        "sign_type", "timestamp", "version", "notify_url",
        "biz_content", "sign",
    ]
    for key in param_order:
        if key in alipay_params:
            ordered_params[key] = alipay_params[key]
    
    for key, val in alipay_params.items():
        if key not in ordered_params:
            ordered_params[key] = val
    
    ordered_params["method"] = "alipay.trade.wap.pay"
    ordered_params["charset"] = "utf-8"
    
    if "biz_content" in ordered_params:
        try:
            biz = json.loads(ordered_params["biz_content"])
            print(f"\nbiz_content 解析: {biz}")
        except:
            biz = {}
        biz["product_code"] = "QUICK_WAP_WAY"
        ordered_params["biz_content"] = json.dumps(biz, separators=(",", ":"), ensure_ascii=True)
        print(f"修改后 biz_content: {ordered_params['biz_content']}")
    
    encoded_data = urlencode(ordered_params)
    print(f"\n编码后数据长度: {len(encoded_data)}")
    
    submit_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Origin": "https://www.yiyipay.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.yiyipay.com/",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Priority": "u=0, i",
    }
    
    resp4 = session.post(
        gateway_url,
        data=encoded_data,
        headers=submit_headers,
        timeout=15,
        allow_redirects=False,
        verify=False
    )
    
    print(f"\n支付宝网关响应:")
    print(f"  状态码: {resp4.status_code}")
    print(f"  Headers: {dict(resp4.headers)}")
    print(f"  响应内容: {resp4.text[:500]}")
    
    if resp4.status_code in [301, 302]:
        location = resp4.headers.get("Location")
        print(f"\n重定向地址: {location}")
    else:
        print("\n未收到重定向响应,可能是参数错误或签名验证失败")
        
else:
    print("未找到支付宝表单!")
