import sys
sys.path.insert(0, r'D:\Project\Qoder\GetPayurl\web\backend')
from app.services.houfaka_service import HoufakaService
from app.database import SessionLocal

# 使用user_id=2（admin用户）
db = SessionLocal()
service = HoufakaService(user_id=2, db=db)

# 加载cookie
loaded = service.load_cookies()
print(f"Cookie loaded: {loaded}")

if loaded:
    # 测试获取商品价格
    product_url = "https://www.houfaka.com/details/E11D52A3"
    print(f"\nTesting product URL: {product_url}")
    
    result = service.get_product_price(product_url)
    print(f"\nResult:")
    print(f"  success: {result['success']}")
    print(f"  product_id: {result.get('product_id')}")
    print(f"  product_name: {result.get('product_name')}")
    print(f"  original_price: {result.get('original_price')}")
    print(f"  stock: {result.get('stock')}")
    
    if service.logs:
        print(f"\nLogs:")
        for log in service.logs:
            print(f"  {log}")
else:
    print("No cookies loaded! Please login first with user_id=2")

db.close()
