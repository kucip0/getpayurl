import requests
from bs4 import BeautifulSoup
import re
import json

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 步骤1-2: 创建订单
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
print(f'创建订单响应: {json.dumps(result, ensure_ascii=False)[:300]}')

# data 可能是dict或list
data = result.get('data', {})
if isinstance(data, list):
    order_url = data[0].get('url', '') if data else ''
elif isinstance(data, dict):
    order_url = data.get('url', '')
else:
    order_url = ''

order_no = order_url.split('/')[-1] if order_url else ''
if not order_no:
    print('未获取到订单号')
    exit(1)
print(f'订单号: {order_no}')

# 步骤3: 访问支付确认页面
print('\n访问支付确认页面')
pay_url = f'https://www.xinfaka.com/paymentconfirm/{order_no}'
resp2 = session.get(pay_url, timeout=15)
html2 = resp2.text
soup2 = BeautifulSoup(html2, 'html.parser')

# 保存HTML到文件
with open('payment_page.html', 'w', encoding='utf-8') as f:
    f.write(html2)
print('页面已保存到 payment_page.html')

# 分析页面结构
print('\n查找支付链接或二维码:')

# 查找所有链接
links = soup2.find_all('a', href=True)
for link in links:
    href = link.get('href')
    text = link.get_text().strip()
    if href and ('pay' in href.lower() or 'alipay' in href.lower() or 'http' in href):
        print(f'链接: {href}')
        print(f'文本: {text}')

# 查找iframe
iframes = soup2.find_all('iframe')
for iframe in iframes:
    src = iframe.get('src')
    print(f'\niframe src: {src}')

# 查找表单
forms = soup2.find_all('form')
for form in forms:
    print(f'\n表单 action: {form.get("action")}')
    for inp in form.find_all('input', {'type': 'hidden'}):
        print(f'  {inp.get("name")} = {inp.get("value")[:60]}')

# 查找二维码或支付链接相关的div
pay_divs = soup2.find_all('div', class_=re.compile('.*pay.*|.*qr.*|.*code.*', re.I))
for div in pay_divs[:5]:
    print(f'\nDIV class: {div.get("class")}')
    print(f'内容: {div.get_text().strip()[:200]}')

# 查找所有script
scripts = soup2.find_all('script')
for script in scripts:
    if script.string and ('payment' in script.string.lower() or 'qr' in script.string.lower() or 'pay' in script.string.lower()):
        print(f'\n脚本内容:')
        print(script.string[:300])
