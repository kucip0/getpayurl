import requests
from bs4 import BeautifulSoup
import re
import json
import time

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({
    'User-Agent': MOBILE_UA
})

print('=== 步骤1: 访问商品页面 ===')
url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
csrf_token = csrf_match.group(1) if csrf_match else ''
print(f'CSRF Token: {csrf_token[:20]}...')

goods_id = soup.find('input', {'id': 'GoodsId'})
shop_id = soup.find('input', {'id': 'shopId'})

# 查找支付方式列表
print('\n=== 查找支付方式 ===')
pay_list = soup.find('ul', {'class': 'pay_list'})
if not pay_list:
    pay_list = soup.find('ul', class_=re.compile('.*pay.*'))

if pay_list:
    print(f'找到支付列表: {pay_list.get("class")}')
    items = pay_list.find_all('li')
    for item in items:
        print(f'  支付方式: data-id={item.get("data-id")}, type={item.get("data-type")}, ident={item.get("data-ident")}')
else:
    # 尝试其他方式查找
    print('未找到支付列表,查找所有li元素...')
    li_with_pay = soup.find_all('li', attrs={'data-type': True})
    for li in li_with_pay:
        print(f'  data-id={li.get("data-id")}, type={li.get("data-type")}, ident={li.get("data-ident")}')

# 查找隐藏的支付方式字段
print('\n=== 查找支付相关隐藏字段 ===')
hidden_fields = soup.find_all('input', {'type': 'hidden'})
for field in hidden_fields:
    name = field.get('name', '')
    if 'pay' in name.lower() or 'type' in name.lower():
        print(f'  {field.get("name")} = {field.get("value")}')

# 查找表单
print('\n=== 查找表单 ===')
forms = soup.find_all('form')
for idx, form in enumerate(forms):
    print(f'表单 {idx}: id={form.get("id")}, action={form.get("action")}')
    for inp in form.find_all('input', {'type': 'hidden'}):
        name = inp.get('name')
        if name:
            print(f'  {name} = {inp.get("value")[:50]}...')
