import requests
from bs4 import BeautifulSoup
import re
import json
import time

# 移动端 User-Agent
MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({
    'User-Agent': MOBILE_UA
})

print('=== 步骤1: 访问商品页面(移动端UA) ===')
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
print(f'状态码: {resp.status_code}')

html = resp.text
soup = BeautifulSoup(html, 'html.parser')

title = soup.find('title')
print(f'页面标题: {title.get_text().strip() if title else "无"}')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f'CSRF Token: {csrf_token[:30]}...')

goods_id = soup.find('input', {'id': 'GoodsId'})
shop_id = soup.find('input', {'id': 'shopId'})
goods_price = soup.find('input', {'id': 'goodsPrice'})

if goods_id:
    print(f'GoodsId: {goods_id.get("value")}')
if shop_id:
    print(f'shopId: {shop_id.get("value")[:30]}...')
if goods_price:
    print(f'goodsPrice: {goods_price.get("value")}')

print('\n=== 步骤2: 获取商品列表 ===')
headers = {
    'X-CSRF-TOKEN': csrf_token,
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
    'Referer': url,
}
resp2 = session.post('https://www.xinfaka.com/goods/getlist', json={}, headers=headers, timeout=15)
print(f'状态码: {resp2.status_code}')
try:
    data = resp2.json()
    print(f'响应: {json.dumps(data, ensure_ascii=False)[:200]}')
except:
    print(f'响应: {resp2.text[:200]}')

print('\n=== 步骤3: 创建订单 ===')
order_data = {
    'GoodsId': goods_id.get('value') if goods_id else '1100',
    'quantity': '1',
    'shopId': shop_id.get('value') if shop_id else '',
    'contact': '13812345678',
    'email': '',
    'couponcode': '',
    'paymoney': '1.00',
    'danjia': '1.00',
    'price': '1.00',
    'kucun': '10',
    'feePayer': '2',
    'fee_rate': '0.05',
    'min_fee': '0.1',
    'rate': '100',
    'pid': '47',
}

headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
resp3 = session.post('https://www.xinfaka.com/goods/createorder', data=order_data, headers=headers, timeout=15)
print(f'状态码: {resp3.status_code}')

try:
    result = resp3.json()
    print(f'响应: {json.dumps(result, ensure_ascii=False)[:300]}')
    order_no = result.get('order_id') or result.get('trade_no')
    if order_no:
        print(f'订单号: {order_no}')
except Exception as e:
    print(f'解析JSON失败: {e}')
    order_no = None

if not order_no:
    print('未获取到订单号,测试结束')
    exit(1)

print(f'\n=== 步骤4: 获取支付确认页面 ===')
pay_url = f'https://www.xinfaka.com/paymentconfirm/{order_no}'
resp4 = session.get(pay_url, timeout=15)
print(f'状态码: {resp4.status_code}')
print(f'页面标题: {soup4.find("title").get_text().strip() if (soup4 := BeautifulSoup(resp4.text, "html.parser")).find("title") else "无"}')

if '支付宝' in resp4.text:
    print('页面包含支付宝')
if '确认付款' in resp4.text:
    print('页面包含确认付款按钮')

form = soup4.find('form')
if form:
    print(f'找到表单 action={form.get("action")}')

print(f'\n=== 步骤5: 轮询订单状态 ===')
check_url = f'https://www.xinfaka.com/checkorder/{order_no}'
headers['Content-Type'] = 'application/json'

for i in range(5):
    print(f'轮询 {i+1}/5...')
    resp5 = session.post(check_url, json={}, headers=headers, timeout=15)
    try:
        result = resp5.json()
        print(f'响应: {json.dumps(result, ensure_ascii=False)[:200]}')
        
        data = result.get('data', {})
        status = result.get('status', '')
        
        if data.get('payment_url') or data.get('qr_code_data') or data.get('redirect_url'):
            pay_link = data.get('payment_url') or data.get('qr_code_data') or data.get('redirect_url')
            print(f'\n✅ 获取到支付链接: {pay_link}')
            break
        
        if status == 'paid':
            print('订单已支付')
            break
    except Exception as e:
        print(f'解析失败: {e}')
    
    time.sleep(2)

print('\n测试完成')
