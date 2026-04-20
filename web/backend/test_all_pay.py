import requests
from bs4 import BeautifulSoup
import re

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text

# 提取所有支付相关HTML
pay_section_match = re.search(r'(<ul[^>]*class=["\'][^"\']*pay[^"\']*["\'][^>]*>.*?</ul>)', html, re.DOTALL)
if pay_section_match:
    print('=== 支付列表HTML ===')
    print(pay_section_match.group(1)[:500])

# 或者查找所有包含 data-id 的元素
print('\n=== 所有包含data-id的元素 ===')
data_id_elems = re.findall(r'<li([^>]*data-id[^>]*)>', html)
for elem in data_id_elems:
    print(elem)

# 查找是否有支付宝logo或文字
if '支付宝' in html or 'zfb' in html or 'alipay' in html.lower():
    print('\n页面包含支付宝相关文字')
    # 找到上下文
    for match in re.finditer(r'.{50}支付宝.{50}', html):
        print(match.group())
        print('---')
