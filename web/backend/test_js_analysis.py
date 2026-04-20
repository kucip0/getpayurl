import requests
from bs4 import BeautifulSoup
import re

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

url = 'https://www.xinfaka.com/single/8BF70AA3E39D'
resp = session.get(url, timeout=15)
html = resp.text

# 查找所有 script 标签
soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script', src=True)
print('=== 外部 JS 文件 ===')
for script in scripts:
    src = script.get('src')
    print(src)

# 查找内联 JS 中包含支付选择逻辑的
print('\n=== 查找支付选择相关JS ===')
inline_scripts = soup.find_all('script')
for idx, script in enumerate(inline_scripts):
    if script.string and ('payType' in script.string or 'data-id' in script.string or 'createorder' in script.string):
        print(f'\n内联脚本 {idx}:')
        # 提取关键部分
        lines = script.string.split('\n')
        for line in lines:
            if 'payType' in line or 'data-id' in line or 'createorder' in line or '支付' in line:
                print(line.strip()[:200])
