# GetPayurl Web - Ubuntu 服务器新手部署指南

> 本指南专为零基础新手设计，从零开始教你如何在 Ubuntu 服务器上部署 GetPayurl 项目。

---

## 📋 部署前准备清单

在开始之前，请确保你已准备好以下内容：

### 1. 云服务器
- 推荐平台：阿里云、腾讯云、华为云、AWS、Vultr、DigitalOcean
- 操作系统：**Ubuntu 22.04 LTS**（必须）
- 配置要求：1核CPU / 2GB内存 / 20GB硬盘（最低配置）
- 网络：需要公网 IP 地址

### 2. 本地工具
- **SSH 客户端**：
  - Windows：推荐使用 [MobaXterm](https://mobaxterm.mobatek.net/) 或 [PuTTY](https://www.putty.org/)
  - Mac/Linux：系统自带终端即可
- **文件传输工具**（可选）：
  - Windows：WinSCP
  - Mac：Cyberduck
  - 命令行：scp 命令

### 3. 域名（可选）
- 如果有域名，需要先解析到服务器 IP
- 没有域名也可以用 IP 地址访问

---

## 🚀 完整部署流程

### 第一步：连接到 Ubuntu 服务器

#### Windows 用户（使用 MobaXterm）

1. **下载并安装 MobaXterm**
   - 访问：https://mobaxterm.mobatek.net/download-home-edition.html
   - 下载 "Installer edition" 版本
   - 双击安装

2. **创建 SSH 连接**
   - 打开 MobaXterm
   - 点击左上角 "Session"
   - 选择 "SSH"
   - 填写以下信息：
     ```
     Remote host: 你的服务器IP地址（例如：47.123.45.67）
     Specify username: root（或你的用户名）
     Port: 22
     ```
   - 点击 "OK"
   - 首次连接会提示 "Are you sure you want to continue connecting?"，输入 `yes`
   - 输入密码（输入时不显示，正常）

3. **连接成功标志**
   ```bash
   Welcome to Ubuntu 22.04 LTS
   root@your-server:~#
   ```
   看到类似上面的提示，说明连接成功！

#### Mac/Linux 用户（使用终端）

打开终端，输入以下命令：

```bash
# 连接到服务器（替换 IP 地址）
ssh root@47.123.45.67

# 首次连接会提示，输入 yes
# 然后输入密码
```

---

### 第二步：检查服务器环境

连接成功后，先检查系统是否符合要求：

```bash
# 1. 检查 Ubuntu 版本
cat /etc/os-release

# 应该看到类似输出：
# NAME="Ubuntu"
# VERSION="22.04 LTS"

# 2. 检查内存
free -h

# 3. 检查磁盘空间
df -h

# 4. 检查网络连接
ping -c 3 baidu.com
```

**如果以上检查都正常，继续下一步。**

---

### 第三步：上传项目文件到服务器

有两种方法可以上传项目：

#### 方法 A：使用 Git 克隆（推荐）

```bash
# 1. 安装 Git
apt update
apt install -y git

# 2. 创建项目目录
mkdir -p /opt/getpayurl
cd /opt/getpayurl

# 3. 克隆项目（替换为你的仓库地址）
git clone https://github.com/kucip0/getpayurl.git .

# 4. 查看文件
ls -la
```

应该看到以下文件：
```
install.sh
DEPLOY.md
web/
...
```

#### 方法 B：使用 SCP 上传（本地操作）

在你的本地电脑上打开终端（Windows 使用 Git Bash 或 PowerShell）：

```bash
# 1. 进入项目目录
cd D:\Project\Qoder\GetPayurl

# 2. 压缩项目（排除不必要的文件）
# Windows PowerShell:
Compress-Archive -Path * -DestinationPath getpayurl.zip -Force

# Mac/Linux:
zip -r getpayurl.zip . -x "*.git*" "node_modules/*" "venv/*" "__pycache__/*" "*.pyc"

# 3. 上传到服务器（替换 IP 地址）
scp getpayurl.zip root@47.123.45.67:/opt/

# 4. SSH 登录服务器
ssh root@47.123.45.67

# 5. 在服务器上解压
cd /opt
apt install -y unzip
unzip getpayurl.zip -d getpayurl
cd getpayurl
```

---

### 第四步：运行一键部署脚本

项目文件上传成功后，运行部署脚本：

```bash
# 1. 确保在正确的目录
cd /opt/getpayurl

# 2. 检查 install.sh 是否存在
ls -l install.sh

# 应该看到：-rwxr-xr-x ... install.sh

# 3. 如果权限不对，添加执行权限
chmod +x install.sh

# 4. 运行部署脚本（需要 root 权限）
sudo bash install.sh
```

### 部署脚本会自动完成以下工作：

```
✅ 检查系统环境（Ubuntu 版本、root 权限）
✅ 更新系统包
✅ 安装 Python 3.11
✅ 安装 Node.js 18
✅ 安装 Nginx
✅ 创建 Python 虚拟环境
✅ 安装所有 Python 依赖
✅ 安装所有 Node.js 依赖
✅ 生成安全的环境变量（SECRET_KEY）
✅ 构建前端项目
✅ 配置 Nginx 反向代理
✅ 创建 systemd 服务
✅ 启动后端服务
✅ 配置防火墙（UFW）
✅ 验证部署结果
```

### 脚本运行过程中的交互：

脚本会提示你输入以下信息（直接回车使用默认值）：

```
域名（如：example.com） [localhost]: 
→ 如果你有域名，输入域名；如果没有，直接回车使用 localhost

安装目录 [/opt/getpayurl]: 
→ 直接回车使用默认目录

后端端口 [8000]: 
→ 直接回车使用默认端口
```

### 部署成功的标志：

看到以下输出表示部署成功：

```
==============================================
部署完成！
==============================================

访问地址：
  前端：http://localhost
  API文档：http://localhost/api/docs

管理命令：
  查看后端日志：sudo journalctl -u getpayurl-backend -f
  重启服务：sudo systemctl restart getpayurl-backend nginx
  ...

==============================================
祝使用愉快！
```

---

### 第五步：验证部署结果

#### 1. 检查服务状态

```bash
# 检查后端服务
sudo systemctl status getpayurl-backend

# 应该看到绿色圆点 ● 和 "active (running)"

# 检查 Nginx
sudo systemctl status nginx

# 应该看到绿色圆点 ● 和 "active (running)"
```

#### 2. 测试后端 API

```bash
# 测试 API 是否响应
curl http://127.0.0.1:8000

# 应该返回：
# {"message":"GetPayurl Web API","version":"1.0.0"}
```

#### 3. 浏览器访问

在你的本地电脑浏览器中访问：

- **如果使用 IP 地址**：`http://你的服务器IP`
- **如果有域名**：`http://yourdomain.com`

应该能看到 GetPayurl Web 的登录页面！

#### 4. 检查防火墙

```bash
# 查看防火墙状态
sudo ufw status

# 应该看到：
# 22/tcp     ALLOW
# 80/tcp     ALLOW
# 443/tcp    ALLOW
```

---

## 🔧 常用管理命令

### 查看日志

```bash
# 查看后端实时日志
sudo journalctl -u getpayurl-backend -f

# 查看最近 100 行日志
sudo journalctl -u getpayurl-backend -n 100

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/getpayurl-access.log

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/getpayurl-error.log
```

### 服务管理

```bash
# 重启后端服务
sudo systemctl restart getpayurl-backend

# 重启 Nginx
sudo systemctl restart nginx

# 重启所有服务
sudo systemctl restart getpayurl-backend nginx

# 查看服务状态
sudo systemctl status getpayurl-backend

# 停止服务
sudo systemctl stop getpayurl-backend

# 启动服务
sudo systemctl start getpayurl-backend
```

### 数据库备份

```bash
# 手动备份
sudo /opt/getpayurl/backup.sh

# 备份文件保存在：/opt/getpayurl/backups/

# 查看备份文件
ls -lh /opt/getpayurl/backups/
```

### 更新部署

如果你修改了代码，需要重新部署：

```bash
# 方法1：使用更新脚本
sudo /opt/getpayurl/deploy.sh

# 方法2：手动更新
cd /opt/getpayurl

# 如果是 Git 仓库，拉取最新代码
git pull

# 重新安装依赖并构建
cd web/backend
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
npm run build

# 重启服务
sudo systemctl restart getpayurl-backend nginx
```

---

## 🐛 常见问题排查

### 问题1：无法访问网站

**症状**：浏览器显示 "无法访问此网站" 或 "连接超时"

**排查步骤**：

```bash
# 1. 检查 Nginx 是否运行
sudo systemctl status nginx

# 如果不运行，启动它
sudo systemctl start nginx

# 2. 检查防火墙
sudo ufw status

# 如果 80 端口没有 ALLOW，添加它
sudo ufw allow 80/tcp

# 3. 检查云服务器安全组
# 登录你的云服务器控制台
# 确保安全组规则允许 80 端口（HTTP）和 443 端口（HTTPS）
```

### 问题2：后端服务未启动

**症状**：API 返回 502 Bad Gateway

**排查步骤**：

```bash
# 1. 检查后端服务状态
sudo systemctl status getpayurl-backend

# 2. 查看错误日志
sudo journalctl -u getpayurl-backend -n 50

# 3. 常见错误及解决方法：

# 错误：ModuleNotFoundError
# 解决：重新安装依赖
cd /opt/getpayurl/web/backend
source venv/bin/activate
pip install -r requirements.txt

# 错误：端口被占用
# 解决：检查端口占用
sudo lsof -i:8000
# 杀死占用端口的进程
sudo kill -9 <PID>

# 4. 重启服务
sudo systemctl restart getpayurl-backend
```

### 问题3：前端页面空白或报错

**排查步骤**：

```bash
# 1. 检查前端构建产物是否存在
ls -la /opt/getpayurl/web/frontend/dist/

# 应该有 index.html 和 assets 目录

# 2. 重新构建前端
cd /opt/getpayurl/web/frontend
npm install
npm run build

# 3. 检查 Nginx 配置
sudo nginx -t

# 4. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/getpayurl-error.log
```

### 问题4：权限问题

**症状**：Permission denied

**解决方法**：

```bash
# 设置正确的权限
sudo chown -R www-data:www-data /opt/getpayurl
sudo chmod -R 755 /opt/getpayurl
sudo chmod 664 /opt/getpayurl/web/backend/getpayurl.db
```

### 问题5：数据库损坏

**解决方法**：

```bash
# 1. 停止服务
sudo systemctl stop getpayurl-backend

# 2. 备份当前数据库（如果还能访问）
cp /opt/getpayurl/web/backend/getpayurl.db /opt/getpayurl/web/backend/getpayurl.db.old

# 3. 删除损坏的数据库
sudo rm /opt/getpayurl/web/backend/getpayurl.db

# 4. 重启服务（会自动创建新数据库）
sudo systemctl start getpayurl-backend
```

---

## 📞 获取帮助

如果遇到问题，可以通过以下方式获取帮助：

1. **查看完整部署文档**：`DEPLOY.md`
2. **查看项目 README**：`web/README.md`
3. **查看后端日志**：`sudo journalctl -u getpayurl-backend -f`
4. **查看 Nginx 日志**：`sudo tail -f /var/log/nginx/getpayurl-error.log`

---

## 📚 附录

### A. SSH 连接命令速查

```bash
# 基本连接
ssh root@服务器IP

# 指定端口连接（如果不是默认 22 端口）
ssh -p 2222 root@服务器IP

# 使用密钥文件连接
ssh -i /path/to/private_key root@服务器IP
```

### B. 文件传输命令速查

```bash
# 从本地上传文件到服务器
scp 本地文件路径 root@服务器IP:远程路径

# 从服务器下载文件到本地
scp root@服务器IP:远程文件路径 本地路径

# 上传整个目录
scp -r 本地目录 root@服务器IP:远程路径
```

### C. 重要文件路径

| 文件/目录 | 路径 | 说明 |
|-----------|------|------|
| 项目根目录 | `/opt/getpayurl` | 项目安装位置 |
| 后端代码 | `/opt/getpayurl/web/backend` | Python 后端 |
| 前端代码 | `/opt/getpayurl/web/frontend` | Vue.js 前端 |
| 数据库 | `/opt/getpayurl/web/backend/getpayurl.db` | SQLite 数据库 |
| 环境变量 | `/opt/getpayurl/.env` | 环境配置 |
| 部署脚本 | `/opt/getpayurl/install.sh` | 一键部署脚本 |
| Nginx 配置 | `/etc/nginx/sites-available/getpayurl` | Nginx 配置 |
| systemd 服务 | `/etc/systemd/system/getpayurl-backend.service` | 后端服务 |
| 后端日志 | `/var/log/getpayurl/` | 后端运行日志 |
| Nginx 日志 | `/var/log/nginx/` | Nginx 访问日志 |

### D. 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 22 | SSH | 远程连接（必须开放） |
| 80 | HTTP | Web 访问 |
| 443 | HTTPS | 加密 Web 访问 |
| 8000 | 后端 API | FastAPI 服务（仅本机访问） |

---

**文档版本**：1.0.0  
**最后更新**：2026-04-14  
**适用系统**：Ubuntu 22.04 LTS / 24.04 LTS  
**适用版本**：GetPayurl Web 1.0.0

---

## 🎉 恭喜！

如果你已经完成了以上所有步骤，说明你的 GetPayurl Web 已经成功部署到服务器上了！

接下来你可以：
1. 访问网站注册账号
2. 登录系统
3. 配置平台（四云发卡/猴发卡）
4. 添加商品链接
5. 生成支付二维码

祝使用愉快！🚀
