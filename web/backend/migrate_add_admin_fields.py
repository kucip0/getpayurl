"""
数据库迁移脚本：添加用户管理字段
为已有用户表添加 is_admin 和 is_disabled 字段
并将 "admin" 用户设置为管理员
"""

import sqlite3
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def migrate():
    """执行数据库迁移"""
    # 获取数据库路径
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    print(f"连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查并添加 is_admin 字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            print("添加 is_admin 字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0 NOT NULL")
        else:
            print("is_admin 字段已存在")
        
        # 检查并添加 is_disabled 字段
        if 'is_disabled' not in columns:
            print("添加 is_disabled 字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_disabled INTEGER DEFAULT 0 NOT NULL")
        else:
            print("is_disabled 字段已存在")
        
        # 将 admin 用户设置为管理员
        print("设置 admin 用户为管理员...")
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
        affected = cursor.rowcount
        if affected > 0:
            print(f"成功设置 {affected} 个 admin 用户为管理员")
        else:
            print("警告: 未找到 admin 用户")
        
        # 提交更改
        conn.commit()
        
        # 验证结果
        cursor.execute("SELECT id, username, is_admin, is_disabled FROM users")
        users = cursor.fetchall()
        print("\n用户列表:")
        print(f"{'ID':<5} {'用户名':<20} {'管理员':<10} {'状态':<10}")
        print("-" * 45)
        for user in users:
            status = "已禁用" if user[3] == 1 else "正常"
            admin_flag = "是" if user[2] == 1 else "否"
            print(f"{user[0]:<5} {user[1]:<20} {admin_flag:<10} {status:<10}")
        
        print("\n迁移完成!")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
