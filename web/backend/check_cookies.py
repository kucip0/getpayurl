import sqlite3
import json

conn = sqlite3.connect('D:/Project/Qoder/GetPayurl/web/backend/getpayurl.db')
cursor = conn.cursor()
cursor.execute("SELECT cookies FROM platform_configs WHERE platform_code='houfaka'")
row = cursor.fetchone()

if row and row[0]:
    cookies = json.loads(row[0])
    print(f'Cookies count: {len(cookies)}')
    for c in cookies:
        print(f"  {c['name']}: {c['value'][:30]}...")
else:
    print('No cookies found')

conn.close()
