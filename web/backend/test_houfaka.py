import sys
sys.path.insert(0, r'D:\Project\Qoder\GetPayurl\web\backend')
from app.services.houfaka_service import HoufakaService
from app.database import SessionLocal
import requests

# 创建数据库会话
db = SessionLocal()

# 创建服务实例
service = HoufakaService(user_id=1, db=db)

# 加载cookie
loaded = service.load_cookies()
print(f"Cookie loaded: {loaded}")
print(f"Session cookies: {dict(service.session.cookies)}")

# 测试获取商品价格
product_url = "https://www.houfaka.com/details/E11D52A3"
print(f"\nTesting product URL: {product_url}")

# 直接发起请求看看
resp = service.session.get(product_url)
print(f"Response status: {resp.status_code}")
print(f"Response length: {len(resp.text)}")

# 保存HTML到文件
with open('D:/test_houfaka.html', 'w', encoding='utf-8') as f:
    f.write(resp.text)
print("HTML saved to D:/test_houfaka.html")

# 测试解析
html = resp.text.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

price_span = soup.find('span', class_='card__detail_price')
print(f"\nPrice span found: {price_span is not None}")
if price_span:
    print(f"Price text: {price_span.get_text().strip()}")

goods_box = soup.find('div', class_='goods_box')
print(f"Goods box found: {goods_box is not None}")
if goods_box:
    h3 = goods_box.find('h3')
    print(f"H3 found: {h3 is not None}")
    if h3:
        print(f"Product name: {h3.get_text().strip()}")

db.close()
