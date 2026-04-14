import sys
sys.path.insert(0, r'D:\Project\Qoder\GetPayurl\web\backend')
from app.database import SessionLocal
from app.models import PlatformConfig
import json

db = SessionLocal()

# 检查所有用户的平台配置
configs = db.query(PlatformConfig).all()
print(f'Total platform configs: {len(configs)}')
for config in configs:
    print(f'\nConfig ID={config.id}:')
    print(f'  user_id: {config.user_id}')
    print(f'  platform_code: {config.platform_code}')
    print(f'  shop_username: {config.shop_username}')
    print(f'  has cookies: {config.cookies is not None}')
    if config.cookies:
        try:
            cookies = json.loads(config.cookies)
            print(f'  cookies count: {len(cookies)}')
            for c in cookies[:3]:
                print(f"    {c['name']}: {c['value'][:20]}...")
        except:
            print(f'  cookies: (parse error)')

db.close()
