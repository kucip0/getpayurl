import requests
from bs4 import BeautifulSoup
import re

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 创建订单
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)
goods_id = BeautifulSoup(html, 'html.parser').find('input', {'id': 'GoodsId'}).get('value')
shop_id = BeautifulSoup(html, 'html.parser').find('input', {'id': 'shopId'}).get('value')

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
order_no = order_url.split('/')[-1]
print(f'订单号: {order_no}')

# 访问/payment
url1 = f'https://www.xinfaka.com/payment/{order_no}'
resp1 = session.get(url1, timeout=15, allow_redirects=False)
url2 = resp1.headers.get('Location')

# 访问/disburse  
resp2 = session.get(url2, timeout=15, allow_redirects=False)
url3 = resp2.headers.get('Location')

# 访问yiypipay
print(f'\n访问 yiypipay: {url3}')
resp3 = session.get(url3, timeout=15)
print(f'状态码: {resp3.status_code}')

# 解析表单
soup = BeautifulSoup(resp3.text, 'html.parser')
form = soup.find('form', {'id': 'alipaysubmit'})
if form:
    action = form.get('action')
    print(f'表单 action: {action}')
    
    # 提取所有隐藏字段
    print('\n表单字段:')
    for inp in form.find_all('input', {'type': 'hidden'}):
        name = inp.get('name')
        value = inp.get('value')
        if name:
            print(f'  {name} = {value[:60]}...')
    
    print(f'\n✅ 支付宝支付链接: {action}')
else:
    print('未找到alipaysubmit表单')
    # 保存HTML查看
    with open('yiyipay_page.html', 'w', encoding='utf-8') as f:
        f.write(resp3.text)
    print('页面已保存到 yiyipay_page.html')
