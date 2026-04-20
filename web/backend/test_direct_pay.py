import requests
from bs4 import BeautifulSoup
import re
import json

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 步骤1: 创建订单
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

# 步骤2: 直接访问支付页面 /payment/{订单号}
print(f'\n访问支付页面: /payment/{order_no}')
pay_url = f'https://www.xinfaka.com/payment/{order_no}'
resp2 = session.get(pay_url, timeout=15, allow_redirects=True)

print(f'状态码: {resp2.status_code}')
print(f'最终URL: {resp2.url}')
print(f'Content-Type: {resp2.headers.get("Content-Type")}')

# 检查是否有跳转
if resp2.url != pay_url:
    print(f'发生了跳转! 跳转到: {resp2.url}')
    
# 检查响应内容
if 'alipay' in resp2.text.lower() or '支付宝' in resp2.text:
    print('页面包含支付宝相关内容')
    
# 查找支付链接或二维码
soup2 = BeautifulSoup(resp2.text, 'html.parser')

# 查找所有链接
links = soup2.find_all('a', href=True)
for link in links:
    href = link.get('href')
    if 'http' in href:
        print(f'链接: {href}')

# 查找iframe
iframes = soup2.find_all('iframe', src=True)
for iframe in iframes:
    src = iframe.get('src')
    print(f'iframe: {src}')

# 查找二维码
qrcodes = soup2.find_all('div', id=re.compile('.*qr.*|.*code.*', re.I))
for qr in qrcodes:
    print(f'二维码div: {qr.get("id")}')

# 保存HTML
with open('alipay_page.html', 'w', encoding='utf-8') as f:
    f.write(resp2.text)
print(f'\n页面已保存到 alipay_page.html')
