import requests
from bs4 import BeautifulSoup
import re
import json
import time

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 步骤1: 访问商品页面
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
print('步骤1: 访问商品页面')
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)
goods_id = soup.find('input', {'id': 'GoodsId'}).get('value')
shop_id = soup.find('input', {'id': 'shopId'}).get('value')
print(f'GoodsId: {goods_id}, shopId: {shop_id[:20]}...')

# 步骤2: 创建订单
print('\n步骤2: 创建订单')
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
print(f'响应: {json.dumps(result, ensure_ascii=False)}')

data = result.get('data', {})
if isinstance(data, list) and data:
    order_url = data[0].get('url', '')
elif isinstance(data, dict):
    order_url = data.get('url', '')
else:
    order_url = ''

if not order_url:
    msg = result.get('msg', '未知错误')
    print(f'创建订单失败: {msg}')
    exit(1)

order_no = order_url.split('/')[-1]
print(f'订单号: {order_no}')

# 步骤3: 访问支付确认页面
print('\n步骤3: 访问支付确认页面')
pay_url = f'https://www.xinfaka.com/paymentconfirm/{order_no}'
resp2 = session.get(pay_url, timeout=15)
html2 = resp2.text

# 保存HTML
with open('payment_page.html', 'w', encoding='utf-8') as f:
    f.write(html2)
print(f'页面已保存到 payment_page.html')

soup2 = BeautifulSoup(html2, 'html.parser')

# 查找支付链接
print('\n查找支付相关链接:')

# 查找所有href包含pay或http的a标签
links = soup2.find_all('a', href=True)
for link in links:
    href = link.get('href')
    if 'http' in href or 'pay' in href.lower():
        print(f'a链接: {href}')

# 查找iframe
iframes = soup2.find_all('iframe')
for iframe in iframes:
    src = iframe.get('src')
    print(f'iframe: {src}')

# 查找form
forms = soup2.find_all('form')
for form in forms:
    print(f'\nform action: {form.get("action")}')
    for inp in form.find_all('input', {'type': 'hidden'}):
        name = inp.get('name')
        value = inp.get('value')
        if name:
            print(f'  {name} = {value[:60] if value else ""}')

# 查找script中的支付链接
scripts = soup2.find_all('script')
for script in scripts:
    if script.string and ('payment' in script.string.lower() or 'qr' in script.string.lower()):
        print(f'\n脚本内容:')
        print(script.string[:300])
