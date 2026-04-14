#!/bin/bash

###############################################################################
# GetPayurl Web - Ubuntu 一键部署脚本
# 适用系统：Ubuntu 22.04 LTS / 24.04 LTS
# 使用方法：sudo bash install.sh
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 用户运行此脚本：sudo bash install.sh"
        exit 1
    fi
}

# 检查操作系统
check_os() {
    if [ ! -f /etc/os-release ]; then
        log_error "无法检测操作系统"
        exit 1
    fi
    
    source /etc/os-release
    
    if [ "$ID" != "ubuntu" ]; then
        log_error "此脚本仅支持 Ubuntu 系统，当前系统：$ID"
        exit 1
    fi
    
    log_info "检测到操作系统：Ubuntu $VERSION_ID"
}

# 检查是否是交互式终端
if [ -t 0 ]; then
    INTERACTIVE=true
else
    INTERACTIVE=false
fi

# 获取用户输入
get_input() {
    local prompt="$1"
    local default="$2"
    local input
    
    if [ "$INTERACTIVE" = true ]; then
        read -p "$prompt [$default]: " input
        echo "${input:-$default}"
    else
        echo "$default"
    fi
}

###############################################################################
# 主部署流程
###############################################################################

echo "=============================================="
echo "  GetPayurl Web - Ubuntu 一键部署脚本"
echo "  版本：1.0.0"
echo "=============================================="
echo ""

# 1. 检查环境
log_info "检查运行环境..."
check_root
check_os

# 2. 获取配置
echo ""
log_info "请配置以下信息（直接回车使用默认值）："
DOMAIN=$(get_input "域名（如：example.com）" "localhost")
INSTALL_DIR=$(get_input "安装目录" "/opt/getpayurl")
BACKEND_PORT=$(get_input "后端端口" "8000")

echo ""
log_info "配置信息："
echo "  域名：$DOMAIN"
echo "  安装目录：$INSTALL_DIR"
echo "  后端端口：$BACKEND_PORT"
echo ""

if [ "$INTERACTIVE" = true ]; then
    read -p "确认开始部署？(y/n) " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "部署已取消"
        exit 0
    fi
fi

# 3. 更新系统
log_info "更新系统包..."
apt update -qq
apt upgrade -y -qq
log_success "系统更新完成"

# 4. 安装依赖
log_info "安装系统依赖..."
apt install -y -qq \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    software-properties-common \
    nginx \
    > /dev/null 2>&1
log_success "系统依赖安装完成"

# 5. 安装 Python 3.11
if command -v python3.11 &> /dev/null; then
    log_success "Python 3.11 已安装，跳过：$(python3.11 --version)"
else
    log_info "安装 Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y > /dev/null 2>&1
    apt update -qq > /dev/null 2>&1
    apt install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip > /dev/null 2>&1

    # 验证 Python
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python 3.11 安装失败"
        exit 1
    fi
    log_success "Python 3.11 安装完成：$(python3.11 --version)"
fi

# 确保 venv 和 dev 包也已安装
apt install -y -qq python3.11-venv python3.11-dev python3-pip > /dev/null 2>&1

# 6. 安装 Node.js 18
if command -v node &> /dev/null; then
    log_success "Node.js 已安装，跳过：$(node --version)"
else
    log_info "安装 Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
    apt install -y -qq nodejs > /dev/null 2>&1

    # 验证 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 安装失败"
        exit 1
    fi
    log_success "Node.js 安装完成：$(node --version)"
fi

# 7. 创建项目目录
log_info "创建项目目录：$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 8. 克隆或复制项目
if [ -d ".git" ]; then
    log_info "检测到 Git 仓库，跳过克隆"
else
    log_warning "请在 $INSTALL_DIR 目录下手动放置项目文件"
    log_info "或者使用：git clone <项目地址> $INSTALL_DIR"
fi

# 9. 安装后端依赖
log_info "安装后端 Python 依赖..."
cd "$INSTALL_DIR/web/backend"

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖（先安装固定版本的 bcrypt，避免兼容性问题）
pip install --upgrade pip -q
pip install bcrypt==3.2.2 -q
pip install -r requirements.txt -q

log_success "后端依赖安装完成"

# 10. 配置环境变量
log_info "生成环境变量配置..."
cd "$INSTALL_DIR"

SECRET_KEY=$(openssl rand -hex 32)

cat > .env << EOF
# 应用配置
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 数据库配置
DATABASE_URL=sqlite:///./web/backend/getpayurl.db

# CORS配置
ALLOWED_ORIGINS=["http://localhost:5173", "http://$DOMAIN"]
EOF

log_success "环境变量配置完成"

# 11. 安装前端依赖并构建
log_info "安装前端依赖..."
cd "$INSTALL_DIR/web/frontend"
npm install --silent

log_info "构建前端项目..."
npm run build --silent

log_success "前端构建完成"

# 12. 配置 Nginx
log_info "配置 Nginx..."

cat > /etc/nginx/sites-available/getpayurl << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # 前端静态文件
    location / {
        root $INSTALL_DIR/web/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
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
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/getpayurl /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
if nginx -t > /dev/null 2>&1; then
    systemctl reload nginx
    log_success "Nginx 配置完成"
else
    log_error "Nginx 配置测试失败"
    exit 1
fi

# 13. 创建 systemd 服务
log_info "创建后端 systemd 服务..."

cat > /etc/systemd/system/getpayurl-backend.service << EOF
[Unit]
Description=GetPayurl Backend Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$INSTALL_DIR/web/backend
Environment="PATH=$INSTALL_DIR/web/backend/venv/bin"
ExecStart=$INSTALL_DIR/web/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT --workers 4
Restart=always
RestartSec=3
StandardOutput=append:/var/log/getpayurl/backend.log
StandardError=append:/var/log/getpayurl/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

# 创建日志目录
mkdir -p /var/log/getpayurl
chown www-data:www-data /var/log/getpayurl

# 设置权限
chown -R www-data:www-data "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# 启动服务
systemctl daemon-reload
systemctl enable getpayurl-backend
systemctl start getpayurl-backend

# 等待服务启动
sleep 2

# 检查服务状态
if systemctl is-active --quiet getpayurl-backend; then
    log_success "后端服务启动成功"
else
    log_error "后端服务启动失败，请查看日志：journalctl -u getpayurl-backend"
    exit 1
fi

# 14. 配置防火墙
log_info "配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp > /dev/null 2>&1
    ufw allow 80/tcp > /dev/null 2>&1
    ufw allow 443/tcp > /dev/null 2>&1
    ufw --force enable > /dev/null 2>&1
    log_success "防火墙配置完成"
else
    log_warning "未检测到 UFW，跳过防火墙配置"
fi

# 15. 创建快捷脚本
log_info "创建管理脚本..."

# 部署脚本
cat > "$INSTALL_DIR/deploy.sh" << 'DEPLOY_EOF'
#!/bin/bash
echo "开始部署更新..."
cd /opt/getpayurl/web/backend
source venv/bin/activate
pip install -r requirements.txt -q
cd ../frontend
npm install --silent
npm run build --silent
sudo systemctl restart getpayurl-backend
sudo systemctl reload nginx
echo "部署完成！"
DEPLOY_EOF

chmod +x "$INSTALL_DIR/deploy.sh"

# 备份脚本
cat > "$INSTALL_DIR/backup.sh" << 'BACKUP_EOF'
#!/bin/bash
BACKUP_DIR="/opt/getpayurl/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /opt/getpayurl/web/backend/getpayurl.db $BACKUP_DIR/getpayurl_$DATE.db
echo "备份完成：$BACKUP_DIR/getpayurl_$DATE.db"
BACKUP_EOF

chmod +x "$INSTALL_DIR/backup.sh"

# 16. 验证部署
log_info "验证部署..."

# 检查后端 API
sleep 2
if curl -s http://127.0.0.1:$BACKEND_PORT | grep -q "GetPayurl"; then
    log_success "后端 API 响应正常"
else
    log_warning "后端 API 可能未完全启动，请稍后检查"
fi

# 17. 完成
echo ""
echo "=============================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=============================================="
echo ""
echo "访问地址："
if [ "$DOMAIN" = "localhost" ]; then
    echo "  前端：http://localhost"
    echo "  API文档：http://localhost/api/docs"
else
    echo "  前端：http://$DOMAIN"
    echo "  API文档：http://$DOMAIN/api/docs"
fi
echo ""
echo "管理命令："
echo "  查看后端日志：sudo journalctl -u getpayurl-backend -f"
echo "  重启服务：sudo systemctl restart getpayurl-backend nginx"
echo "  查看服务状态：sudo systemctl status getpayurl-backend"
echo "  备份数据库：sudo $INSTALL_DIR/backup.sh"
echo "  更新部署：sudo $INSTALL_DIR/deploy.sh"
echo ""
echo "重要文件："
echo "  环境变量：$INSTALL_DIR/.env"
echo "  数据库：$INSTALL_DIR/web/backend/getpayurl.db"
echo "  Nginx配置：/etc/nginx/sites-available/getpayurl"
echo ""
echo "=============================================="
log_success "祝使用愉快！"
