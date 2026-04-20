import requests
from bs4 import BeautifulSoup
import re
import json
import time

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

print('步骤1: 访问商品页面')
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)

goods_id = soup.find('input', {'id': 'GoodsId'}).get('value')
shop_id = soup.find('input', {'id': 'shopId'}).get('value')

print('步骤2: 创建订单')
order_data = {
    'GoodsId': goods_id,
    'quantity': '1',
    'shopId': shop_id,
    'is_sms': '0',
    'sms_receive': '',
    'take_card_password': '',
    'payId': '18',
    'payType': '1',
    'coupon': '',
    'is_xh': '0',
    'kami_id': '',
    'is_dk': '0',
    'visit_password': '',
}

headers = {
    'X-CSRF-TOKEN': csrf_token,
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Referer': url,
}

resp = session.post('https://www.xinfaka.com/goods/createorder', data=order_data, headers=headers, timeout=15)
result = resp.json()
url_from_resp = result.get('data', {}).get('url', '')
order_no = url_from_resp.split('/')[-1]
print(f'订单号: {order_no}')

print('\n步骤3: 访问支付确认页面')
pay_url = f'https://www.xinfaka.com/paymentconfirm/{order_no}'
resp2 = session.get(pay_url, timeout=15)
print(f'状态码: {resp2.status_code}')

print('\n步骤4: 检查轮询接口响应')
check_url = f'https://www.xinfaka.com/checkorder/{order_no}'
headers['Content-Type'] = 'application/json'

resp3 = session.post(check_url, json={}, headers=headers, timeout=15)
print(f'状态码: {resp3.status_code}')
print(f'Content-Type: {resp3.headers.get("Content-Type")}')
print(f'响应文本: {resp3.text[:500]}')

# 尝试解析
try:
    data = resp3.json()
    print(f'JSON: {json.dumps(data, ensure_ascii=False)[:500]}')
except:
    print('不是JSON格式')

# 检查是否有跳转
print(f'最终URL: {resp3.url}')
