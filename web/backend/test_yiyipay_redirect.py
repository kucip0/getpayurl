import requests
from bs4 import BeautifulSoup
import re

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

# 创建订单(简化)
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
order_no = order_url.split('/')[-1] if order_url else ''
print(f'订单号: {order_no}')

# 跟踪重定向
print('\n重定向链:')
url = f'https://www.xinfaka.com/payment/{order_no}'
for i in range(5):
    resp = session.get(url, timeout=15, allow_redirects=False)
    print(f'{i+1}. {resp.status_code} -> ', end='')
    
    if resp.status_code in [301, 302, 303, 307, 308]:
        url = resp.headers.get('Location')
        print(url)
        
        # 如果是yiypipay,继续跟踪
        if 'yiyipay' in url:
            # yiypipay 可能会继续重定向
            resp2 = session.get(url, timeout=15, allow_redirects=False)
            print(f'{i+2}. {resp2.status_code} -> ', end='')
            
            if resp2.status_code in [301, 302]:
                url3 = resp2.headers.get('Location')
                print(url3)
                print(f'\n最终支付宝链接: {url3}')
                break
            else:
                print(f'yiypipay未重定向')
                # 检查HTML中的JS跳转
                soup = BeautifulSoup(resp2.text, 'html.parser')
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and ('location' in script.string.lower() or 'alipay' in script.string.lower()):
                        print(f'Script: {script.string[:200]}')
                break
    else:
        print('最终URL')
        break
