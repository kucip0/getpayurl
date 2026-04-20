import requests
from bs4 import BeautifulSoup

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

order_no = 'XFK260419171214759215'
url = f'https://www.xinfaka.com/disburse/{order_no}'

resp = session.get(url, timeout=15)
print(f'状态码: {resp.status_code}')
print(f'\n=== HTML内容 ===')
print(resp.text[:1000])

# 保存完整HTML
with open('disburse_page.html', 'w', encoding='utf-8') as f:
    f.write(resp.text)
print('\n页面已保存到 disburse_page.html')
