import requests
import json

MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1'

session = requests.Session()
session.headers.update({'User-Agent': MOBILE_UA})

print('=== 测试支付链接重定向 ===\n')

# 使用之前成功的订单号
order_no = 'XFK260419171214759215'

# 步骤1: 访问 /payment/{order_no}
pay_url = f'https://www.xinfaka.com/payment/{order_no}'
print(f'步骤1: 访问 {pay_url}')

resp1 = session.get(pay_url, timeout=15, allow_redirects=False)
print(f'状态码: {resp1.status_code}')

if resp1.status_code in [301, 302, 303, 307, 308]:
    redirect_1 = resp1.headers.get('Location')
    print(f'第一次重定向: {redirect_1}')
    
    # 步骤2: 访问 yiypipay.com
    print(f'\n步骤2: 访问 {redirect_1}')
    resp2 = session.get(redirect_1, timeout=15, allow_redirects=False)
    print(f'状态码: {resp2.status_code}')
    
    if resp2.status_code in [301, 302, 303, 307, 308]:
        redirect_2 = resp2.headers.get('Location')
        print(f'第二次重定向(支付宝): {redirect_2}')
        print(f'\n✅ 最终支付宝支付链接: {redirect_2}')
    else:
        print('yiypipay 没有重定向')
        print(f'使用URL: {redirect_1}')
else:
    print('没有第一次重定向')
