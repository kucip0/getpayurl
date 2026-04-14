import sys
sys.path.insert(0, r'D:\Project\Qoder\GetPayurl\web\backend')
from app.database import SessionLocal
from app.models import PlatformConfig
import json

db = SessionLocal()

# 查询平台配置
config = db.query(PlatformConfig).filter(
    PlatformConfig.user_id == 1,
    PlatformConfig.platform_code == 'houfaka'
).first()

print(f'Config found: {config is not None}')
if config:
    print(f'Config ID: {config.id}')
    print(f'Has cookies: {config.cookies is not None}')
    print(f'Cookies length: {len(config.cookies) if config.cookies else 0}')
    
    if config.cookies:
        try:
            cookies = json.loads(config.cookies)
            print(f'Parsed cookies count: {len(cookies)}')
            for c in cookies:
                print(f"  {c['name']}: {c['value'][:20]}...")
        except Exception as e:
            print(f'JSON parse error: {e}')
else:
    print('Config not found for user_id=1, platform_code=houfaka')

db.close()
