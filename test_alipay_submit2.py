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
url2 = resp1.headers.get("Location")

resp2 = session.get(url2, headers=headers, timeout=15, allow_redirects=False, verify=False)
url3 = resp2.headers.get("Location")

resp3 = session.get(url3, headers=headers, timeout=15, verify=False)

# 提取支付宝表单
soup = BeautifulSoup(resp3.text, "html.parser")
form = soup.find("form", {"id": "alipaysubmit"})
alipay_params = {}
for inp in form.find_all("input", {"type": "hidden"}):
    name = inp.get("name")
    value = inp.get("value")
    if name and value is not None:
        alipay_params[name] = value

# 提交到支付宝网关
print("提交到支付宝网关...")
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
    except:
        biz = {}
    biz["product_code"] = "QUICK_WAP_WAY"
    ordered_params["biz_content"] = json.dumps(biz, separators=(",", ":"), ensure_ascii=True)

encoded_data = urlencode(ordered_params)

submit_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Cache-Control": "max-age=0",
    "Origin": "https://www.yiyipay.com",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://www.yiyipay.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

resp4 = session.post(
    gateway_url,
    data=encoded_data,
    headers=submit_headers,
    timeout=15,
    allow_redirects=False,
    verify=False
)

print(f"支付宝网关响应状态码: {resp4.status_code}")
print(f"Content-Type: {resp4.headers.get('Content-Type', '')}")

# 如果返回200,说明需要解析HTML并自动提交表单
if resp4.status_code == 200:
    print("\n解析支付宝返回的HTML...")
    soup4 = BeautifulSoup(resp4.text, "html.parser")
    
    # 查找是否有表单需要提交
    forms = soup4.find_all("form")
    print(f"找到 {len(forms)} 个表单")
    
    for i, form in enumerate(forms):
        print(f"\n表单 {i}:")
        print(f"  action: {form.get('action', '')}")
        print(f"  method: {form.get('method', '')}")
        print(f"  id: {form.get('id', '')}")
        print(f"  name: {form.get('name', '')}")
        
        inputs = form.find_all("input", {"type": "hidden"})
        print(f"  隐藏字段数: {len(inputs)}")
        for inp in inputs[:3]:
            print(f"    {inp.get('name')}: {inp.get('value', '')[:50]}...")
    
    # 查找script中的跳转逻辑
    scripts = soup4.find_all("script")
    print(f"\n找到 {len(scripts)} 个脚本")
    for i, script in enumerate(scripts):
        if script.string and ("location" in script.string or "redirect" in script.string or "submit" in script.string):
            print(f"\n脚本 {i} 包含跳转/提交逻辑:")
            print(script.string[:300])
