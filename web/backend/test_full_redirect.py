import requests

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

print('=== 完整跟踪支付链接重定向 ===\n')

order_no = 'XFK260419171214759215'

# 第1次
url1 = f'https://www.xinfaka.com/payment/{order_no}'
print(f'1. {url1}')
resp1 = session.get(url1, timeout=15, allow_redirects=False)
print(f'   状态: {resp1.status_code}')

if resp1.status_code in [301, 302]:
    url2 = resp1.headers.get('Location')
    print(f'   -> {url2}\n')
    
    # 第2次
    print(f'2. {url2}')
    resp2 = session.get(url2, timeout=15, allow_redirects=False)
    print(f'   状态: {resp2.status_code}')
    
    if resp2.status_code in [301, 302]:
        url3 = resp2.headers.get('Location')
        print(f'   -> {url3}\n')
        
        # 第3次
        print(f'3. {url3}')
        resp3 = session.get(url3, timeout=15, allow_redirects=False)
        print(f'   状态: {resp3.status_code}')
        
        if resp3.status_code in [301, 302]:
            url4 = resp3.headers.get('Location')
            print(f'   -> {url4}\n')
            print(f'✅ 最终URL: {url4}')
        else:
            print(f'   最终URL: {url3}')
    else:
        print(f'   最终URL: {url2}')
else:
    print(f'   最终URL: {url1}')
