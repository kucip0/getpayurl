# GetPayurl Web - Ubuntu 部署指南

## 快速开始（推荐）

### 方法一：已有项目文件（推荐）

如果你已经将项目文件上传到服务器：

```bash
# 1. SSH 登录服务器
ssh root@your-server-ip

# 2. 进入项目目录
cd /opt/getpayurl

# 3. 运行部署脚本
sudo bash install.sh
```

### 方法二：从 Git 克隆（推荐）

```bash
# 1. SSH 登录服务器
ssh root@your-server-ip

# 2. 克隆项目
git clone <项目地址> /opt/getpayurl
cd /opt/getpayurl

# 3. 运行部署脚本
sudo bash install.sh
```

### 方法三：使用 SCP 上传

在本地电脑上：

```bash
# 压缩项目
zip -r getpayurl.zip GetPayurl/ -x "*.git*" "node_modules/*" "venv/*"

# 上传到服务器
scp getpayurl.zip root@your-server-ip:/opt/

# SSH 登录服务器
ssh root@your-server-ip

# 解压并部署
cd /opt
unzip getpayurl.zip
mv GetPayurl getpayurl
cd getpayurl
sudo bash install.sh
```

### 方法四：手动创建脚本

如果脚本文件不存在，可以直接在服务器创建：

```bash
# SSH 登录服务器
ssh root@your-server-ip

# 创建目录
mkdir -p /opt/getpayurl
cd /opt/getpayurl

# 手动或使用编辑器创建 install.sh
nano install.sh
# 粘贴 install.sh 内容，保存退出

# 添加权限并运行
chmod +x install.sh
sudo bash install.sh
```

脚本会自动完成：
- ✅ 安装 Python 3.11 和 Node.js 18
- ✅ 安装所有依赖包
- ✅ 配置环境变量
- ✅ 构建前端项目
- ✅ 配置 Nginx 反向代理
- ✅ 创建 systemd 服务
- ✅ 配置防火墙
- ✅ 验证部署结果

运行过程中会提示输入：
- **域名**：你的网站域名（默认：localhost）
- **安装目录**：项目安装位置（默认：/opt/getpayurl）
- **后端端口**：API服务端口（默认：8000）

---

## 项目概述

GetPayurl Web 是一个基于 FastAPI + Vue.js 3 的支付二维码生成平台，支持多个发卡平台（四云发卡、猴发卡等）的订单处理和二维码生成。

### 技术栈

**后端**
- Python 3.11
- FastAPI 0.100+
- SQLAlchemy 2.0+
- SQLite（默认数据库）
- Uvicorn（ASGI服务器）

**前端**
- Vue.js 3.3+
- Vite 5.0+
- Element Plus 2.3+
- Pinia（状态管理）
- Axios（HTTP客户端）

---

## 一、系统要求

### 操作系统
- **Ubuntu 22.04 LTS**（推荐）或 **Ubuntu 24.04 LTS**

### 硬件要求
| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 1核心 | 2核心及以上 |
| 内存 | 2GB | 4GB及以上 |
| 硬盘 | 2GB可用空间 | 5GB及以上 |

### 网络要求
- 服务器需要能够访问外网（下载依赖包）
- 开放端口：80（HTTP）、443（HTTPS）、8000（后端API）

---

## 二、环境安装

### 2.1 更新系统

```bash
# 更新包列表
sudo apt update

# 升级已安装的包
sudo apt upgrade -y

# 安装必要的基础工具
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    software-properties-common
```

### 2.2 安装 Python 3.11

```bash
# 添加 deadsnakes PPA（提供最新Python版本）
sudo add-apt-repository ppa:deadsnakes/ppa -y

# 更新包列表
sudo apt update

# 安装 Python 3.11 及开发工具
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 验证安装
python3.11 --version
# 应输出：Python 3.11.x

# 安装 pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# 验证 pip
python3.11 -m pip --version
```

### 2.3 安装 Node.js 18.x LTS

```bash
# 方法1：使用 NodeSource 仓库（推荐）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version
# 应输出：v18.x.x

npm --version
# 应输出：9.x.x 或 10.x.x
```

### 2.4 安装 Nginx（生产环境）

```bash
# 安装 Nginx
sudo apt install -y nginx

# 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 验证安装
nginx -v
# 应输出：nginx version: nginx/1.x.x

# 检查 Nginx 状态
sudo systemctl status nginx
```

---

## 三、项目下载

### 3.1 克隆项目

```bash
# 创建项目目录
mkdir -p /opt/getpayurl
cd /opt/getpayurl

# 克隆项目（替换为实际的项目地址）
git clone <项目地址> .

# 或手动下载并解压项目文件到 /opt/getpayurl
```

### 3.2 项目结构

```
/opt/getpayurl/
├── web/
│   ├── backend/              # 后端项目
│   │   ├── app/              # 应用代码
│   │   ├── requirements.txt  # Python依赖
│   │   └── getpayurl.db      # SQLite数据库（自动生成）
│   └── frontend/             # 前端项目
│       ├── src/              # 源代码
│       ├── package.json      # Node.js依赖
│       └── vite.config.js    # Vite配置
├── .env                      # 环境变量配置
└── DEPLOY.md                 # 部署文档
```

---

## 四、后端部署

### 4.1 安装 Python 依赖

```bash
# 进入后端目录
cd /opt/getpayurl/web/backend

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装完成后验证
pip list
# 应看到 fastapi、uvicorn、sqlalchemy 等包
```

### 4.2 配置环境变量

```bash
# 返回项目根目录
cd /opt/getpayurl

# 创建 .env 文件
cat > .env << 'EOF'
# 应用配置
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 数据库配置
DATABASE_URL=sqlite:///./web/backend/getpayurl.db

# CORS配置（根据实际域名修改）
ALLOWED_ORIGINS=["http://localhost:5173", "http://yourdomain.com"]
EOF

# 生成 SECRET_KEY 并替换
SECRET_KEY=$(openssl rand -hex 32)
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env

# 查看生成的配置
cat .env
```

### 4.3 启动后端服务

#### 开发模式（测试用）

```bash
# 激活虚拟环境
cd /opt/getpayurl/web/backend
source venv/bin/activate

# 启动服务
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 看到以下输出表示启动成功：
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

#### 生产模式（使用 systemd）

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/getpayurl-backend.service
```

写入以下内容：

```ini
[Unit]
Description=GetPayurl Backend Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/getpayurl/web/backend
Environment="PATH=/opt/getpayurl/web/backend/venv/bin"
ExecStart=/opt/getpayurl/web/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3
StandardOutput=append:/var/log/getpayurl/backend.log
StandardError=append:/var/log/getpayurl/backend-error.log

[Install]
WantedBy=multi-user.target
```

创建日志目录并设置权限：

```bash
# 创建日志目录
sudo mkdir -p /var/log/getpayurl
sudo chown www-data:www-data /var/log/getpayurl

# 设置项目目录权限
sudo chown -R www-data:www-data /opt/getpayurl
sudo chmod -R 755 /opt/getpayurl
sudo chmod 664 /opt/getpayurl/web/backend/getpayurl.db 2>/dev/null || true
```

启动服务：

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable getpayurl-backend

# 启动服务
sudo systemctl start getpayurl-backend

# 查看服务状态
sudo systemctl status getpayurl-backend

# 查看日志
sudo journalctl -u getpayurl-backend -f

# 重启服务
sudo systemctl restart getpayurl-backend
```

### 4.4 验证后端

```bash
# 测试 API
curl http://127.0.0.1:8000
# 应返回：{"message":"GetPayurl Web API","version":"1.0.0"}

# 如果在本地测试，也可以访问
curl http://localhost:8000/docs
```

---

## 五、前端部署

### 5.1 安装 Node.js 依赖

```bash
# 进入前端目录
cd /opt/getpayurl/web/frontend

# 安装依赖
npm install

# 如果遇到权限问题
sudo npm install --unsafe-perm
```

### 5.2 开发模式（测试用）

```bash
# 启动开发服务器
npm run dev

# 访问：http://localhost:5173
```

### 5.3 生产构建

```bash
# 构建生产版本
npm run build

# 构建成功后，产物在 dist 目录
ls -la dist/

# 预览生产构建
npm run preview
# 访问：http://localhost:4173
```

---

## 六、Nginx 配置

### 6.1 创建 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/getpayurl
```

写入以下内容（替换 `yourdomain.com` 为实际域名）：

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 前端静态文件
    location / {
        root /opt/getpayurl/web/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 日志配置
    access_log /var/log/nginx/getpayurl-access.log;
    error_log /var/log/nginx/getpayurl-error.log;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 6.2 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/getpayurl /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t
# 应输出：nginx: the configuration file /etc/nginx/nginx.conf syntax is ok

# 重载 Nginx
sudo systemctl reload nginx
```

### 6.3 配置防火墙

```bash
# 启用 UFW
sudo ufw enable

# 允许 SSH（重要！否则会被锁在外面）
sudo ufw allow 22/tcp

# 允许 HTTP
sudo ufw allow 80/tcp

# 允许 HTTPS
sudo ufw allow 443/tcp

# 查看状态
sudo ufw status
```

---

## 七、配置 HTTPS（Let's Encrypt）

### 7.1 安装 Certbot

```bash
# 安装 Certbot 和 Nginx 插件
sudo apt install -y certbot python3-certbot-nginx
```

### 7.2 获取 SSL 证书

```bash
# 获取并自动配置证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 按照提示：
# 1. 输入邮箱地址
# 2. 同意服务条款（输入 A）
# 3. 是否接收邮件（输入 Y 或 N）
# 4. 选择是否重定向 HTTP 到 HTTPS（推荐选择 2）
```

### 7.3 自动续期

```bash
# 测试自动续期
sudo certbot renew --dry-run

# Certbot 会自动创建定时任务，无需手动配置
# 查看定时任务
sudo systemctl list-timers | grep certbot
```

---

## 八、快速启动脚本

创建一键部署脚本：

```bash
# 创建部署脚本
cat > /opt/getpayurl/deploy.sh << 'EOF'
#!/bin/bash

echo "====================================="
echo "GetPayurl Web - Ubuntu 部署脚本"
echo "====================================="

# 进入项目目录
cd /opt/getpayurl

# 1. 安装后端依赖
echo "[1/4] 安装后端依赖..."
cd web/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..

# 2. 安装前端依赖
echo "[2/4] 安装前端依赖..."
cd web/frontend
npm install
cd ../..

# 3. 构建前端
echo "[3/4] 构建前端..."
cd web/frontend
npm run build
cd ../..

# 4. 重启服务
echo "[4/4] 重启服务..."
sudo systemctl restart getpayurl-backend
sudo systemctl reload nginx

echo ""
echo "====================================="
echo "部署完成！"
echo "访问地址：http://yourdomain.com"
echo "API文档：http://yourdomain.com/api/docs"
echo "====================================="
EOF

# 添加执行权限
chmod +x /opt/getpayurl/deploy.sh

# 运行部署脚本
/opt/getpayurl/deploy.sh
```

---

## 九、常见问题

### 9.1 后端启动失败

**问题**：`ModuleNotFoundError: No module named 'xxx'`

**解决**：
```bash
cd /opt/getpayurl/web/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart getpayurl-backend
```

### 9.2 前端构建失败

**问题**：内存不足

**解决**：
```bash
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### 9.3 502 Bad Gateway

**问题**：Nginx 无法连接到后端

**解决**：
```bash
# 检查后端是否运行
curl http://127.0.0.1:8000

# 查看后端日志
sudo journalctl -u getpayurl-backend -n 50

# 重启后端
sudo systemctl restart getpayurl-backend

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/getpayurl-error.log
```

### 9.4 权限问题

**问题**：`Permission denied`

**解决**：
```bash
# 设置正确的权限
sudo chown -R www-data:www-data /opt/getpayurl
sudo chmod -R 755 /opt/getpayurl
sudo chmod 664 /opt/getpayurl/web/backend/getpayurl.db
```

### 9.5 数据库问题

**问题**：数据库文件不存在或损坏

**解决**：
```bash
# 后端启动时会自动创建数据库
# 如果损坏，删除后重启
sudo rm /opt/getpayurl/web/backend/getpayurl.db
sudo systemctl restart getpayurl-backend
```

---

## 十、系统维护

### 10.1 查看日志

```bash
# 后端日志
sudo journalctl -u getpayurl-backend -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/getpayurl-access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/getpayurl-error.log
```

### 10.2 数据库备份

```bash
# 备份数据库
cp /opt/getpayurl/web/backend/getpayurl.db \
   /opt/getpayurl/web/backend/getpayurl.db.backup.$(date +%Y%m%d)

# 创建备份脚本
cat > /opt/getpayurl/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/getpayurl/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /opt/getpayurl/web/backend/getpayurl.db $BACKUP_DIR/getpayurl_$DATE.db
echo "备份完成：$BACKUP_DIR/getpayurl_$DATE.db"
EOF

chmod +x /opt/getpayurl/backup.sh

# 添加到 crontab（每天凌晨3点备份）
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/getpayurl/backup.sh") | crontab -
```

### 10.3 更新系统

```bash
# 更新后端依赖
cd /opt/getpayurl/web/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 更新前端依赖
cd /opt/getpayurl/web/frontend
npm update
npm run build

# 重启服务
sudo systemctl restart getpayurl-backend
sudo systemctl reload nginx
```

### 10.4 服务管理命令

```bash
# 查看服务状态
sudo systemctl status getpayurl-backend
sudo systemctl status nginx

# 启动服务
sudo systemctl start getpayurl-backend
sudo systemctl start nginx

# 停止服务
sudo systemctl stop getpayurl-backend
sudo systemctl stop nginx

# 重启服务
sudo systemctl restart getpayurl-backend
sudo systemctl restart nginx

# 查看日志
sudo journalctl -u getpayurl-backend -f
```

---

## 十一、使用流程

1. **访问系统**：http://yourdomain.com
2. **注册账号**：点击"注册"按钮
3. **登录系统**：使用注册的账号登录
4. **配置平台**：
   - 进入"平台管理"
   - 选择平台
   - 添加商品链接
   - 保存配置
5. **生成二维码**：
   - 进入"订单处理"
   - 选择平台和商品
   - 设置价格
   - 点击"生成二维码"

---

## 附录

### A. 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端（Nginx） | 80/443 | HTTP/HTTPS |
| 后端API | 8000 | FastAPI/Uvicorn |
| 前端开发 | 5173 | Vite开发服务器 |

### B. 重要文件路径

| 文件/目录 | 路径 |
|-----------|------|
| 项目根目录 | `/opt/getpayurl` |
| 后端代码 | `/opt/getpayurl/web/backend` |
| 前端代码 | `/opt/getpayurl/web/frontend` |
| 数据库 | `/opt/getpayurl/web/backend/getpayurl.db` |
| 环境变量 | `/opt/getpayurl/.env` |
| Nginx配置 | `/etc/nginx/sites-available/getpayurl` |
| systemd服务 | `/etc/systemd/system/getpayurl-backend.service` |
| 后端日志 | `/var/log/getpayurl/` |
| Nginx日志 | `/var/log/nginx/` |

### C. 常用命令速查

```bash
# 部署/更新
/opt/getpayurl/deploy.sh

# 备份数据库
/opt/getpayurl/backup.sh

# 查看后端日志
sudo journalctl -u getpayurl-backend -f

# 重启所有服务
sudo systemctl restart getpayurl-backend nginx

# 进入虚拟环境
cd /opt/getpayurl/web/backend && source venv/bin/activate
```

---

**文档版本**：1.0.0  
**最后更新**：2026-04-13  
**适用系统**：Ubuntu 22.04 LTS / 24.04 LTS  
**适用版本**：GetPayurl Web 1.0.0
