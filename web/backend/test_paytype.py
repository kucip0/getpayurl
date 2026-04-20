import requests
from bs4 import BeautifulSoup
import re
import json

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text
soup = BeautifulSoup(html, 'html.parser')

# 保存完整HTML到文件
with open('page_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('页面已保存到 page_debug.html')

# 查找所有包含支付相关的元素
print('\n=== 查找支付相关元素 ===')
pay_elements = soup.find_all(string=re.compile('支付宝|微信|支付'))
for elem in pay_elements[:10]:
    parent = elem.parent
    print(f'文本: {elem.strip()[:50]}')
    print(f'标签: {parent.name}, class: {parent.get("class")}')
    print(f'父元素: {parent}')
    print()

# 查找所有 li 元素
print('\n=== 所有 li 元素 ===')
lis = soup.find_all('li')
for li in lis[:20]:
    data_id = li.get('data-id')
    data_type = li.get('data-type')
    data_ident = li.get('data-ident')
    if data_id or data_type:
        print(f'data-id={data_id}, data-type={data_type}, data-ident={data_ident}')
        print(f'内容: {li.get_text().strip()[:100]}')
        print()

# 查找表单中的 payType input
print('\n=== payType 字段 ===')
paytype_input = soup.find('input', {'name': 'payType'})
if paytype_input:
    print(f'payType value={paytype_input.get("value")}')
    print(f'完整属性: {paytype_input.attrs}')
