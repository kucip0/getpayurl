# GetPayurl Web 生产环境部署指南

## 适用场景

- 首次部署
- 更新代码（从GitHub拉取最新代码）
- 新增平台支持（趣卡铺、酷卡屋）
- 修复bcrypt兼容性问题

---

## ⚠️ 重要提示：保护生产环境数据

**在执行任何更新操作前，必须先备份以下数据：**

```bash
# 1. 备份数据库（必须）
cp /opt/getpayurl/web/backend/getpayurl.db /opt/getpayurl/web/backend/getpayurl.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. 备份环境变量（必须）
cp /opt/getpayurl/.env /opt/getpayurl/.env.backup.$(date +%Y%m%d_%H%M%S)

# 3. 备份Cookie数据（如存在）
cp -r /opt/getpayurl/web/backend/cookies/ /opt/getpayurl/web/backend/cookies.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
```

**更新原则：**
- ✅ 只更新代码文件，不修改数据库
- ✅ 只更新前端静态资源，不影响用户配置
- ✅ 保留所有已登录平台的Cookie/Session
- ❌ 不要删除或覆盖 `getpayurl.db`
- ❌ 不要删除或覆盖 `.env` 配置文件
- ❌ 不要删除或覆盖 `cookies/` 目录

---

## 方法一：全新部署（推荐用于新服务器）

### 1. 连接服务器

```bash
ssh root@你的服务器IP
```

### 2. 克隆项目

```bash
cd /opt
git clone https://github.com/kucip0/getpayurl.git
cd getpayurl
```

### 3. 运行一键部署脚本

```bash
sudo bash install.sh
```

按提示输入：
- 域名（默认：localhost）
- 安装目录（默认：/opt/getpayurl）
- 后端端口（默认：8000）

### 4. 等待部署完成

脚本会自动完成：
- ✅ 安装系统依赖
- ✅ 安装Python 3.11和Node.js 18
- ✅ 安装正确版本的bcrypt (3.2.2)
- ✅ 配置环境变量
- ✅ 构建前端项目
- ✅ 配置Nginx
- ✅ 创建systemd服务
- ✅ 启动服务

---

## 方法二：更新现有部署（推荐 - 保护生产数据）

### 1. 连接服务器

```bash
ssh root@你的服务器IP
```

### 2. 备份生产数据（必须执行）

```bash
cd /opt/getpayurl

# 备份数据库
cp web/backend/getpayurl.db web/backend/getpayurl.db.backup.$(date +%Y%m%d_%H%M%S)

# 备份环境变量
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 备份Cookie目录（如果存在）
cp -r web/backend/cookies/ web/backend/cookies.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "无cookies目录，跳过"
```

### 3. 拉取最新代码

```bash
cd /opt/getpayurl
git pull origin main
```

### 4. 安装后端依赖

```bash
cd /opt/getpayurl/web/backend
source venv/bin/activate
pip install bcrypt==3.2.2
pip install -r requirements.txt
deactivate
```

### 5. 重新构建前端

```bash
cd /opt/getpayurl/web/frontend
npm install
npm run build
```

### 6. 重启服务

```bash
sudo systemctl restart getpayurl-backend
sudo systemctl reload nginx
```

### 7. 检查服务状态

```bash
sudo systemctl status getpayurl-backend
sudo journalctl -u getpayurl-backend -f --no-pager | tail -50
```

### 8. 验证新增平台

登录系统后，在平台管理页面应该能看到：
- ✅ 趣卡铺（qukapu）
- ✅ 酷卡屋（kukuwu）

---

## 方法三：完全重新部署（最彻底 - 谨慎使用）

**警告：此方法会删除旧项目文件，必须确保已完整备份！**

### 1. 停止现有服务

```bash
sudo systemctl stop getpayurl-backend
sudo systemctl disable getpayurl-backend
```

### 2. 完整备份（必须）

```bash
# 备份数据库
cp /opt/getpayurl/web/backend/getpayurl.db /root/getpayurl_backup_$(date +%Y%m%d).db

# 备份环境变量
cp /opt/getpayurl/.env /root/getpayurl_env_backup_$(date +%Y%m%d)

# 备份Cookie目录（如果存在）
cp -r /opt/getpayurl/web/backend/cookies/ /root/getpayurl_cookies_backup_$(date +%Y%m%d) 2>/dev/null || true

# 下载备份文件到本地（推荐）
scp root@你的服务器IP:/root/getpayurl_backup_*.db ./
```

### 3. 删除旧项目

```bash
rm -rf /opt/getpayurl
```

### 4. 重新克隆

```bash
cd /opt
git clone https://github.com/kucip0/getpayurl.git
cd getpayurl
```

### 5. 运行部署脚本

```bash
sudo bash install.sh
```

### 6. 恢复数据（如果需要）

```bash
# 恢复数据库
cp /root/getpayurl_backup_YYYYMMDD.db /opt/getpayurl/web/backend/getpayurl.db
sudo chown www-data:www-data /opt/getpayurl/web/backend/getpayurl.db

# 恢复环境变量（可选）
cp /root/getpayurl_env_backup_YYYYMMDD /opt/getpayurl/.env

# 恢复Cookie（可选）
cp -r /root/getpayurl_cookies_backup_YYYYMMDD/ /opt/getpayurl/web/backend/cookies/
sudo chown -R www-data:www-data /opt/getpayurl/web/backend/cookies/

# 重启服务
sudo systemctl restart getpayurl-backend
```

---

## 验证部署

### 1. 检查后端API

```bash
curl http://127.0.0.1:8000
```

应该返回：`{"message":"GetPayurl Web API"}`

### 2. 检查前端

浏览器访问：`http://你的服务器IP`

### 3. 验证平台列表

登录系统后，进入"平台管理"页面，应该能看到以下平台：
- ✅ 猴发卡（houfaka）
- ✅ 四云发卡（siyun）
- ✅ 梦言云卡（mengyan）
- ✅ 新发卡（xinfaka）
- ✅ 趣卡铺（qukapu）- **新增**
- ✅ 酷卡屋（kukuwu）- **新增**

### 4. 测试新增平台

1. 选择"趣卡铺"或"酷卡屋"平台
2. 输入店铺账号密码
3. 获取并输入验证码（如果需要）
4. 点击"登录店铺"
5. 登录成功后，尝试生成支付二维码

---

## 常用管理命令

### 查看日志

```bash
# 后端日志
sudo journalctl -u getpayurl-backend -f

# Nginx访问日志
sudo tail -f /var/log/nginx/getpayurl-access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/getpayurl-error.log
```

### 重启服务

```bash
sudo systemctl restart getpayurl-backend
sudo systemctl reload nginx
```

### 查看服务状态

```bash
sudo systemctl status getpayurl-backend
sudo systemctl status nginx
```

### 更新代码

```bash
cd /opt/getpayurl
git pull origin main
cd web/backend && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd ../frontend && npm run build
sudo systemctl restart getpayurl-backend
sudo systemctl reload nginx
```

---

## 常见问题排查

### 问题1：注册失败 500错误

**原因**：bcrypt版本不兼容

**解决**：
```bash
cd /opt/getpayurl/web/backend
source venv/bin/activate
pip install bcrypt==3.2.2
sudo systemctl restart getpayurl-backend
```

### 问题2：前端页面不更新

**原因**：浏览器缓存

**解决**：
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 硬刷新（Ctrl+F5）
3. 或者重新构建前端：
```bash
cd /opt/getpayurl/web/frontend
npm run build
sudo systemctl reload nginx
```

### 问题3：服务启动失败

**检查日志**：
```bash
sudo journalctl -u getpayurl-backend -n 100 --no-pager
```

**常见原因**：
- 端口被占用
- 数据库文件权限错误
- 环境变量配置错误

**解决**：
```bash
# 检查端口
sudo lsof -i :8000

# 修复权限
sudo chown -R www-data:www-data /opt/getpayurl
sudo chmod -R 755 /opt/getpayurl

# 重启服务
sudo systemctl restart getpayurl-backend
```

### 问题4：Nginx 502错误

**原因**：后端服务未启动

**解决**：
```bash
sudo systemctl status getpayurl-backend
sudo systemctl restart getpayurl-backend
sudo systemctl status nginx
```

---

## 重要文件路径

| 文件 | 路径 |
|------|------|
| 后端代码 | `/opt/getpayurl/web/backend/` |
| 前端代码 | `/opt/getpayurl/web/frontend/` |
| 数据库 | `/opt/getpayurl/web/backend/getpayurl.db` |
| 环境变量 | `/opt/getpayurl/.env` |
| Nginx配置 | `/etc/nginx/sites-available/getpayurl` |
| 后端日志 | `/var/log/getpayurl/backend.log` |
| 系统日志 | `journalctl -u getpayurl-backend` |

---

## 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80/443 | 对外访问端口 |
| 后端API | 8000 | 内部服务端口（不对外开放） |

---

## 安全建议

1. **配置HTTPS**（生产环境必须）
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d 你的域名
   ```

2. **修改默认端口**
   在 `.env` 文件中修改 `BACKEND_PORT`

3. **设置防火墙**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

4. **定期备份数据库**
   ```bash
   sudo /opt/getpayurl/backup.sh
   ```

---

## 更新日志

### 2026-04-20
- ✅ 新增趣卡铺平台（qukapu），host: www.qukapu.com
- ✅ 新增酷卡屋平台（kukuwu），host: kkw.yiyipay.com
- ✅ 修复支付二维码获取功能（payId参数修正）
- ✅ 前端添加新平台验证码支持
- ✅ 更新部署文档，增加数据保护说明

### 2026-04-14
- ✅ 修复bcrypt兼容性问题（锁定版本为3.2.2）
- ✅ 修复密码长度限制（72字节）
- ✅ 移除登录页注册入口
- ✅ 优化一键部署脚本
