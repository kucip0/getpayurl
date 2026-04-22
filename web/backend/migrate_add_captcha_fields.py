#!/usr/bin/env python3
"""
数据库迁移脚本：添加验证码 Session 相关字段
解决多 worker 模式下的验证码 Session 丢失问题

新增字段：
- platform_configs.captcha_cookies (TEXT)
- platform_configs.captcha_csrf_token (VARCHAR(500))
"""

import sqlite3
import sys
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'getpayurl.db')

if len(sys.argv) > 1:
    db_path = sys.argv[1]

print(f"数据库路径: {db_path}")

if not os.path.exists(db_path):
    print(f"错误: 数据库文件不存在: {db_path}")
    sys.exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(platform_configs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # 添加 captcha_cookies 字段
    if 'captcha_cookies' not in columns:
        print("添加字段: captcha_cookies")
        cursor.execute("ALTER TABLE platform_configs ADD COLUMN captcha_cookies TEXT")
        print("  [OK] captcha_cookies 字段添加成功")
    else:
        print("  [--] captcha_cookies 字段已存在，跳过")
    
    # 添加 captcha_csrf_token 字段
    if 'captcha_csrf_token' not in columns:
        print("添加字段: captcha_csrf_token")
        cursor.execute("ALTER TABLE platform_configs ADD COLUMN captcha_csrf_token VARCHAR(500)")
        print("  [OK] captcha_csrf_token 字段添加成功")
    else:
        print("  [--] captcha_csrf_token 字段已存在，跳过")
    
    # 提交更改
    conn.commit()
    print("\n数据库迁移完成！")
    
except Exception as e:
    conn.rollback()
    print(f"\n错误: 数据库迁移失败: {str(e)}")
    sys.exit(1)
finally:
    conn.close()
