import requests
from bs4 import BeautifulSoup
import re
import json

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 步骤1: 访问商品页面
print('1. 访问商品页面')
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1)
goods_id = soup.find('input', {'id': 'GoodsId'}).get('value')
shop_id = soup.find('input', {'id': 'shopId'}).get('value')
print(f'GoodsId: {goods_id}, shopId: {shop_id[:20]}...')

# 步骤2: 创建订单
print('\n2. 创建订单')
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
print(f'响应: {json.dumps(result, ensure_ascii=False)[:200]}')

data = result.get('data', {})
if isinstance(data, list) and data:
    order_url = data[0].get('url', '')
elif isinstance(data, dict):
    order_url = data.get('url', '')
else:
    order_url = ''

if not order_url:
    print(f'创建失败: {result.get("msg")}')
    exit(1)

order_no = order_url.split('/')[-1]
print(f'订单号: {order_no}')

# 步骤3: 跟踪重定向
print(f'\n3. 跟踪重定向')
print(f'   /payment/{order_no}')
resp1 = session.get(f'https://www.xinfaka.com/payment/{order_no}', timeout=15, allow_redirects=False)
print(f'   状态: {resp1.status_code}')

if resp1.status_code in [301, 302]:
    url2 = resp1.headers.get('Location')
    print(f'   -> {url2}')
    
    # 继续跟踪
    resp2 = session.get(url2, timeout=15, allow_redirects=False)
    print(f'   状态: {resp2.status_code}')
    
    if resp2.status_code in [301, 302]:
        url3 = resp2.headers.get('Location')
        print(f'   -> {url3}')
        print(f'\n✅ 最终支付链接: {url3}')
    else:
        # 可能是JS跳转,查看HTML
        if 'location' in resp2.text.lower() or 'href' in resp2.text.lower():
            soup2 = BeautifulSoup(resp2.text, 'html.parser')
            scripts = soup2.find_all('script')
            for script in scripts:
                if script.string and ('location' in script.string or 'href' in script.string):
                    print(f'   脚本: {script.string[:200]}')
                    # 提取URL
                    url_match = re.search(r'["\']([^"\']+yiypi[^"\']+)["\']', script.string)
                    if url_match:
                        print(f'   提取到: {url_match.group(1)}')
        else:
            print(f'   最终URL: {url2}')
