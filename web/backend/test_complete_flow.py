import requests
from bs4 import BeautifulSoup
import re
import json
import time

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

print('等待旧订单过期 (10秒)...')
time.sleep(10)

# 步骤1: 访问商品页面
print('\n1. 访问商品页面')
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)
goods_id = soup.find('input', {'id': 'GoodsId'}).get('value')
shop_id = soup.find('input', {'id': 'shopId'}).get('value')
print(f'CSRF: {csrf_token[:20]}..., GoodsId: {goods_id}')

# 步骤2: 创建订单
print('\n2. 创建订单')
order_data = {
    'GoodsId': goods_id, 'quantity': '1', 'shopId': shop_id,
    'is_sms': '0', 'sms_receive': '', 'take_card_password': '',
    'payId': '18', 'payType': '1', 'coupon': '', 'is_xh': '0',
    'kami_id': '', 'is_dk': '0', 'visit_password': '',
}
headers = {
    'X-CSRF-TOKEN': csrf_token, 'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Referer': url,
}

resp = session.post('https://www.xinfaka.com/goods/createorder', data=order_data, headers=headers, timeout=15)
result = resp.json()

data = result.get('data', {})
if isinstance(data, list):
    order_url = data[0].get('url', '') if data else ''
else:
    order_url = data.get('url', '')

if not order_url:
    print(f'创建订单失败: {result.get("msg")}')
    exit(1)

order_no = order_url.split('/')[-1]
print(f'订单号: {order_no}')

# 步骤3: 跟踪重定向获取支付宝链接
print('\n3. 跟踪重定向')

# /payment -> 302
resp1 = session.get(f'https://www.xinfaka.com/payment/{order_no}', timeout=15, allow_redirects=False)
url2 = resp1.headers.get('Location')
print(f'/payment -> {url2}')

# /disburse -> 302
resp2 = session.get(url2, timeout=15, allow_redirects=False)
url3 = resp2.headers.get('Location')
print(f'/disburse -> {url3}')

# yiypipay -> 200 (包含支付宝表单)
resp3 = session.get(url3, timeout=15)
soup3 = BeautifulSoup(resp3.text, 'html.parser')
form = soup3.find('form', {'id': 'alipaysubmit'})

if form and form.get('action'):
    alipay_url = form.get('action')
    print(f'yiypipay -> 支付宝表单 action: {alipay_url[:100]}...')
    print(f'\n✅ 最终支付宝支付链接: {alipay_url}')
else:
    print(f'未找到支付宝表单,使用: {url3}')
