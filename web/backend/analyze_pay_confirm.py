import requests
from bs4 import BeautifulSoup
import re
import json

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 创建订单
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)
goods_id = soup.find('input', {'id': 'GoodsId'}).get('value')
shop_id = soup.find('input', {'id': 'shopId'}).get('value')

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
data = result.get('data', {})
if isinstance(data, list) and data:
    order_url = data[0].get('url', '')
elif isinstance(data, dict):
    order_url = data.get('url', '')
else:
    order_url = ''

order_no = order_url.split('/')[-1]
print(f'订单号: {order_no}')

# 访问支付确认页面
print('\n访问支付确认页面...')
pay_confirm_url = f'https://www.xinfaka.com/paymentconfirm/{order_no}'
resp2 = session.get(pay_confirm_url, timeout=15)
html2 = resp2.text
soup2 = BeautifulSoup(html2, 'html.parser')

# 查找页面中的所有链接和表单
print('\n=== 查找所有链接 ===')
all_links = soup2.find_all('a', href=True)
for link in all_links:
    href = link.get('href')
    text = link.get_text().strip()[:50]
    print(f'链接: {href}')
    print(f'文本: {text}')
    print()

print('\n=== 查找所有表单 ===')
forms = soup2.find_all('form')
for form in forms:
    action = form.get('action')
    method = form.get('method', 'GET')
    print(f'表单 action: {action}, method: {method}')
    for inp in form.find_all('input'):
        name = inp.get('name')
        value = inp.get('value', '')
        input_type = inp.get('type', 'text')
        if name:
            print(f'  {name} ({input_type}) = {value[:50]}')

print('\n=== 查找iframe ===')
iframes = soup2.find_all('iframe', src=True)
for iframe in iframes:
    print(f'iframe src: {iframe.get("src")}')

print('\n=== 查找button ===')
buttons = soup2.find_all('button')
for btn in buttons:
    print(f'button: id={btn.get("id")}, text={btn.get_text().strip()[:50]}')

# 检查页面是否有跳转meta标签
print('\n=== 查找meta跳转 ===')
metas = soup2.find_all('meta', attrs={'http-equiv': 'refresh'})
for meta in metas:
    content = meta.get('content')
    print(f'meta refresh: {content}')

# 保存完整HTML
with open('pay_confirm.html', 'w', encoding='utf-8') as f:
    f.write(html2)
print('\n页面已保存到 pay_confirm.html')
