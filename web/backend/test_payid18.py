import requests
from bs4 import BeautifulSoup
import re
import json
import time

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

print('=== 步骤1: 访问商品页面 ===')
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)

goods_id = soup.find('input', {'id': 'GoodsId'}).get('value')
shop_id = soup.find('input', {'id': 'shopId'}).get('value')

print(f'GoodsId: {goods_id}, shopId: {shop_id[:20]}...')

print('\n=== 步骤2: 创建订单 (payId=18, 支付宝H5) ===')
order_data = {
    'GoodsId': goods_id,
    'quantity': '1',
    'shopId': shop_id,
    'is_sms': '0',
    'sms_receive': '',
    'take_card_password': '',
    'payId': '18',  # 支付宝移动端H5支付
    'payType': '1',  # 支付宝
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
print(f'状态码: {resp.status_code}')

try:
    result = resp.json()
    print(f'响应: {json.dumps(result, ensure_ascii=False)[:300]}')
    # 订单号在 data.url 中
    data = result.get('data', {})
    url_from_resp = data.get('url', '')
    # 从URL中提取订单号
    order_no = url_from_resp.split('/')[-1] if url_from_resp else ''
    if order_no:
        print(f'订单号: {order_no}')
except Exception as e:
    print(f'解析失败: {e}')
    order_no = None

if not order_no:
    print('\n未获取到订单号')
    exit(1)

print(f'\n=== 步骤3: 访问支付确认页面 ===')
pay_url = f'https://www.xinfaka.com/paymentconfirm/{order_no}'
resp2 = session.get(pay_url, timeout=15)
print(f'状态码: {resp2.status_code}')
print(f'页面URL: {resp2.url}')

soup2 = BeautifulSoup(resp2.text, 'html.parser')
title = soup2.find('title')
print(f'页面标题: {title.get_text().strip() if title else "无"}')

print(f'\n=== 步骤4: 轮询订单状态获取支付链接 ===')
check_url = f'https://www.xinfaka.com/checkorder/{order_no}'
headers['Content-Type'] = 'application/json'

for i in range(8):
    print(f'轮询 {i+1}/8...')
    resp3 = session.post(check_url, json={}, headers=headers, timeout=15)
    try:
        result = resp3.json()
        data = result.get('data', {})
        status = result.get('status', '')
        
        if data.get('payment_url') or data.get('qr_code_data') or data.get('redirect_url'):
            pay_link = data.get('payment_url') or data.get('qr_code_data') or data.get('redirect_url')
            print(f'✅ 获取到支付链接: {pay_link[:150]}...')
            print(f'\n完整链接: {pay_link}')
            break
        
        if status == 'paid':
            print('订单已支付')
            break
        
        print(f'状态: {status}')
    except Exception as e:
        print(f'解析失败: {e}')
    
    time.sleep(2)

print('\n测试完成')
