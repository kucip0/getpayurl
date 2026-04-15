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

# 3. 更新系统（使用阿里云镜像源）
log_info "检查APT镜像源配置..."
if grep -q "mirrors.aliyun.com" /etc/apt/sources.list 2>/dev/null; then
    log_success "阿里云APT镜像源已配置，跳过"
else
    log_info "配置阿里云APT镜像源..."
    # 备份原始配置
    cp /etc/apt/sources.list /etc/apt/sources.list.bak 2>/dev/null || true
    cat > /etc/apt/sources.list << 'APT_EOF'
deb http://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ jammy-backports main restricted universe multiverse
APT_EOF
    log_success "阿里云APT镜像源配置完成"
fi

log_info "更新系统包（使用阿里云镜像）..."
apt update -qq
apt upgrade -y -qq
log_success "系统更新完成"

# 4. 安装依赖（逐项检查）
log_info "检查系统依赖..."

# 定义需要安装的包
SYSTEM_PACKAGES="git curl wget build-essential libssl-dev libffi-dev software-properties-common nginx"

# 检查每个包是否已安装
PACKAGES_TO_INSTALL=""
for pkg in $SYSTEM_PACKAGES; do
    if dpkg -s "$pkg" 2>/dev/null | grep -q "Status: install ok installed"; then
        log_success "$pkg 已安装，跳过"
    else
        log_info "$pkg 未安装，将安装"
        PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL $pkg"
    fi
done

# 如果有需要安装的包
if [ -n "$PACKAGES_TO_INSTALL" ]; then
    log_info "安装缺失的系统依赖..."
    apt install -y -qq $PACKAGES_TO_INSTALL > /dev/null 2>&1
    log_success "系统依赖安装完成"
else
    log_success "所有系统依赖已安装，无需更新"
fi

# 5. 安装 Python 3.11（详细检查）
if command -v python3.11 &> /dev/null; then
    log_success "Python 3.11 已安装，跳过：$(python3.11 --version)"
    
    # 检查venv和pip是否可用
    if ! python3.11 -m venv --help &>/dev/null; then
        log_info "python3.11-venv 未安装，正在安装..."
        apt install -y -qq python3.11-venv python3.11-dev python3-pip > /dev/null 2>&1
        log_success "python3.11-venv 安装完成"
    else
        log_success "python3.11-venv 已安装，跳过"
    fi
else
    log_info "安装 Python 3.11..."
    
    # 检查PPA是否已添加
    if ! grep -r "deadsnakes" /etc/apt/sources.list.d/ 2>/dev/null; then
        log_info "添加deadsnakes PPA..."
        add-apt-repository ppa:deadsnakes/ppa -y > /dev/null 2>&1
        apt update -qq > /dev/null 2>&1
    else
        log_success "deadsnakes PPA已添加，跳过"
    fi
    
    apt install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip > /dev/null 2>&1

    # 验证 Python
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python 3.11 安装失败"
        exit 1
    fi
    log_success "Python 3.11 安装完成：$(python3.11 --version)"
fi

# 6. 安装 Node.js 18（详细检查，使用淘宝Node.js镜像）
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge 18 ] 2>/dev/null; then
        log_success "Node.js 已安装（版本 >= 18），跳过：$(node --version)"
    else
        log_warning "Node.js 版本过低（当前：$(node --version)），需要 >= 18，将重新安装..."
        rm -rf /usr/local/node-v*
        rm -f /usr/local/bin/node /usr/local/bin/npm
    fi
fi

if ! command -v node &> /dev/null; then
    log_info "安装 Node.js 18（使用淘宝镜像）..."
    # 使用淘宝镜像源安装Node.js
    curl -fsSL https://npmmirror.com/mirrors/node/v18.20.4/node-v18.20.4-linux-x64.tar.xz -o /tmp/nodejs.tar.xz
    tar -xJf /tmp/nodejs.tar.xz -C /usr/local/
    ln -sf /usr/local/node-v18.20.4-linux-x64/bin/node /usr/local/bin/node
    ln -sf /usr/local/node-v18.20.4-linux-x64/bin/npm /usr/local/bin/npm
    ln -sf /usr/local/node-v18.20.4-linux-x64/bin/npx /usr/local/bin/npx
    rm -f /tmp/nodejs.tar.xz

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

# 9. 安装后端依赖（检查虚拟环境和依赖）
log_info "检查后端Python虚拟环境..."
cd "$INSTALL_DIR/web/backend"

# 检查虚拟环境是否存在
if [ -d "venv" ] && [ -f "venv/bin/python" ] && [ -f "venv/bin/pip" ]; then
    log_success "Python虚拟环境已存在，跳过创建"
else
    log_info "创建Python虚拟环境..."
    python3.11 -m venv venv
    log_success "Python虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 配置pip使用清华镜像（总是执行，确保配置正确）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple >/dev/null 2>&1
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn >/dev/null 2>&1

# 检查pip是否需要更新
CURRENT_PIP=$(pip --version | awk '{print $2}')
log_info "检查pip版本（当前：$CURRENT_PIP）..."
pip install --upgrade pip -q >/dev/null 2>&1

# 检查bcrypt是否已安装
if python -c "import bcrypt" 2>/dev/null; then
    log_success "bcrypt已安装，跳过"
else
    log_info "安装bcrypt..."
    pip install bcrypt==3.2.2 -q
    log_success "bcrypt安装完成"
fi

# 检查requirements.txt中的依赖是否已安装
log_info "检查Python依赖..."
if pip check 2>/dev/null | grep -q "No broken requirements"; then
    log_success "所有Python依赖已正确安装"
else
    log_info "安装/更新Python依赖..."
    pip install -r requirements.txt -q
    log_success "Python依赖安装完成"
fi

log_success "后端环境配置完成"

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

# 11. 安装前端依赖并构建（检查node_modules）
log_info "检查前端依赖..."
cd "$INSTALL_DIR/web/frontend"

# 配置npm使用淘宝镜像（总是执行，确保配置正确）
npm config set registry https://registry.npmmirror.com >/dev/null 2>&1

# 检查node_modules是否存在
if [ -d "node_modules" ]; then
    log_success "node_modules已存在，检查是否需要更新..."
    
    # 检查package-lock.json是否存在
    if [ -f "package-lock.json" ]; then
        # 检查是否有新的依赖需要安装
        if npm outdated >/dev/null 2>&1; then
            log_info "所有npm依赖已是最新版本，无需更新"
        else
            log_info "发现依赖更新，正在安装..."
            npm install --silent
            log_success "npm依赖更新完成"
        fi
    else
        log_info "package-lock.json不存在，执行完整安装..."
        npm install --silent
        log_success "npm依赖安装完成"
    fi
else
    log_info "node_modules不存在，执行完整安装..."
    npm install --silent
    log_success "npm依赖安装完成"
fi

# 检查dist目录是否存在且是最新构建
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    log_success "前端已构建，跳过"
else
    log_info "构建前端项目..."
    npm run build --silent
    log_success "前端构建完成"
fi

# 12. 配置 Nginx（检查是否已配置）
log_info "检查Nginx配置..."

if [ -f /etc/nginx/sites-available/getpayurl ]; then
    log_success "Nginx配置文件已存在，跳过创建"
else
    log_info "创建Nginx配置..."
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
    log_success "Nginx配置创建完成"
fi

# 启用配置（总是执行，确保符号链接正确）
if [ -L /etc/nginx/sites-enabled/getpayurl ]; then
    log_success "Nginx站点已启用，跳过"
else
    ln -sf /etc/nginx/sites-available/getpayurl /etc/nginx/sites-enabled/
    log_success "Nginx站点启用完成"
fi

rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
if nginx -t > /dev/null 2>&1; then
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        log_success "Nginx配置重载完成"
    else
        systemctl start nginx
        log_success "Nginx启动成功"
    fi
else
    log_error "Nginx 配置测试失败"
    exit 1
fi

# 13. 创建 systemd 服务（检查是否已存在）
log_info "检查systemd服务..."

if [ -f /etc/systemd/system/getpayurl-backend.service ]; then
    log_success "systemd服务已存在，跳过创建"
else
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
    log_success "systemd服务创建完成"
fi

# 创建日志目录
if [ -d /var/log/getpayurl ]; then
    log_success "日志目录已存在，跳过创建"
else
    mkdir -p /var/log/getpayurl
    log_success "日志目录创建完成"
fi
chown www-data:www-data /var/log/getpayurl

# 设置权限
chown -R www-data:www-data "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# 启动服务（检查是否需要启动或重启）
systemctl daemon-reload

if systemctl is-active --quiet getpayurl-backend; then
    log_success "后端服务已在运行，跳过启动"
else
    log_info "启动后端服务..."
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
fi

# 14. 配置防火墙（检查规则是否已添加）
log_info "检查防火墙配置..."
if command -v ufw &> /dev/null; then
    # 检查防火墙规则是否已添加
    if ufw status 2>/dev/null | grep -q "80/tcp"; then
        log_success "防火墙规则已配置，跳过"
    else
        log_info "配置防火墙规则..."
        ufw allow 22/tcp > /dev/null 2>&1
        ufw allow 80/tcp > /dev/null 2>&1
        ufw allow 443/tcp > /dev/null 2>&1
        ufw --force enable > /dev/null 2>&1
        log_success "防火墙配置完成"
    fi
else
    log_warning "未检测到 UFW，跳过防火墙配置"
fi

# 15. 创建快捷脚本（检查是否已存在）
log_info "检查管理脚本..."

# 部署脚本
if [ -f "$INSTALL_DIR/deploy.sh" ]; then
    log_success "deploy.sh已存在，跳过创建"
else
    log_info "创建deploy.sh..."
    cat > "$INSTALL_DIR/deploy.sh" << 'DEPLOY_EOF'
#!/bin/bash
echo "=============================================="
echo "  GetPayurl - 更新部署脚本"
echo "=============================================="
echo ""

cd "$INSTALL_DIR"

# 1. 拉取最新代码
echo "[1/5] 拉取最新代码..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "错误：代码拉取失败"
    exit 1
fi
echo "✓ 代码更新完成"
echo ""

# 2. 更新后端依赖（使用清华PyPI镜像）
echo "[2/5] 更新后端依赖..."
cd "$INSTALL_DIR/web/backend"
source venv/bin/activate

# 配置pip使用清华镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

pip install -r requirements.txt -q
echo "✓ 后端依赖更新完成"
echo ""

# 3. 更新前端依赖并构建（使用淘宝npm镜像）
echo "[3/5] 更新前端依赖并构建..."
cd "$INSTALL_DIR/web/frontend"

# 配置npm使用淘宝镜像
npm config set registry https://registry.npmmirror.com

npm install --silent
npm run build --silent
echo "✓ 前端构建完成"
echo ""

# 4. 重启服务
echo "[4/5] 重启后端服务..."
sudo systemctl restart getpayurl-backend
sleep 2

# 检查服务状态
if systemctl is-active --quiet getpayurl-backend; then
    echo "✓ 后端服务重启成功"
else
    echo "✗ 后端服务启动失败，请检查日志：sudo journalctl -u getpayurl-backend -n 50"
    exit 1
fi
echo ""

# 5. 重载Nginx
echo "[5/5] 重载Nginx配置..."
sudo systemctl reload nginx
echo "✓ Nginx重载成功"
echo ""

echo "=============================================="
echo "  ✓ 部署完成！"
echo "=============================================="
echo ""
echo "提示："
echo "  - 查看实时日志：sudo journalctl -u getpayurl-backend -f"
echo "  - 查看服务状态：sudo systemctl status getpayurl-backend"
echo "  - 备份数据库：sudo $INSTALL_DIR/backup.sh"
DEPLOY_EOF
    chmod +x "$INSTALL_DIR/deploy.sh"
    log_success "deploy.sh创建完成"
fi

# 备份脚本
if [ -f "$INSTALL_DIR/backup.sh" ]; then
    log_success "backup.sh已存在，跳过创建"
else
    log_info "创建backup.sh..."
    cat > "$INSTALL_DIR/backup.sh" << 'BACKUP_EOF'
#!/bin/bash
BACKUP_DIR="/opt/getpayurl/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /opt/getpayurl/web/backend/getpayurl.db $BACKUP_DIR/getpayurl_$DATE.db
echo "备份完成：$BACKUP_DIR/getpayurl_$DATE.db"
BACKUP_EOF
    chmod +x "$INSTALL_DIR/backup.sh"
    log_success "backup.sh创建完成"
fi

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
