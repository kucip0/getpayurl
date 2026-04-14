# GetPayurl Web版本设计文档

**日期**: 2026-04-12  
**状态**: 待实现  
**作者**: Qoder

---

## 1. 概述

将现有的PC桌面应用（猴发卡和四云发卡两个平台）转换为Web版本，采用前后端分离架构，支持多用户认证系统。

### 1.1 核心目标

- 复用现有PC版本的业务逻辑（6步支付流程、登录模块、商品管理）
- 提供Web界面，支持多用户独立使用
- 采用直接部署方式，简化运维
- 不修改现有PC版本代码

### 1.2 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | >=0.100.0 |
| 前端框架 | Vue.js | 3.x |
| UI组件库 | Element Plus | 2.x |
| 数据库 | SQLite | 3.x |
| ORM | SQLAlchemy | 2.x |
| 认证 | JWT (python-jose) | 3.x |
| 构建工具 | Vite | 5.x |
| HTTP客户端 | Axios | 1.x |

---

## 2. 项目结构

```
D:\Project\Qoder\GetPayurl\web\
├── backend/                          # 后端项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI应用入口
│   │   ├── config.py                 # 应用配置
│   │   ├── database.py               # SQLite数据库连接
│   │   ├── models.py                 # SQLAlchemy数据库模型
│   │   ├── schemas.py                # Pydantic请求/响应模型
│   │   ├── auth.py                   # JWT认证工具
│   │   ├── dependencies.py           # 依赖注入
│   │   │
│   │   ├── routers/                  # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 注册/登录接口
│   │   │   ├── platforms.py          # 平台管理接口
│   │   │   ├── orders.py             # 订单处理接口
│   │   │   └── config.py             # 配置管理接口
│   │   │
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── base_service.py       # 基础服务类
│   │   │   ├── houfaka_service.py    # 猴发卡业务逻辑
│   │   │   └── siyun_service.py      # 四云发卡业务逻辑
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── http_client.py        # HTTP会话管理
│   │       ├── html_parser.py        # HTML解析
│   │       └── qr_generator.py       # 二维码生成
│   │
│   ├── requirements.txt              # Python依赖
│   └── .env                          # 环境变量
│
├── frontend/                         # 前端项目
│   ├── src/
│   │   ├── views/                    # 页面组件
│   │   │   ├── Login.vue             # 登录页
│   │   │   ├── Register.vue          # 注册页
│   │   │   ├── Dashboard.vue         # 控制台首页
│   │   │   ├── PlatformManage.vue    # 平台管理
│   │   │   ├── OrderProcess.vue      # 订单处理
│   │   │   └── Settings.vue          # 系统设置
│   │   │
│   │   ├── components/               # 可复用组件
│   │   │   ├── PlatformSelector.vue  # 平台选择器
│   │   │   ├── LoginForm.vue         # 店铺登录表单
│   │   │   ├── PriceEditor.vue       # 价格编辑器
│   │   │   ├── QRCodeDisplay.vue     # 二维码显示
│   │   │   ├── LogViewer.vue         # 日志查看器
│   │   │   └── UrlConfigEditor.vue   # URL配置编辑器
│   │   │
│   │   ├── api/                      # API调用模块
│   │   │   ├── index.js              # Axios实例配置
│   │   │   ├── auth.js               # 认证API
│   │   │   ├── platforms.js          # 平台API
│   │   │   ├── orders.js             # 订单API
│   │   │   └── config.js             # 配置API
│   │   │
│   │   ├── stores/                   # Pinia状态管理
│   │   │   ├── auth.js               # 认证状态
│   │   │   ├── platform.js           # 平台状态
│   │   │   └── order.js              # 订单状态
│   │   │
│   │   ├── router/                   # 路由配置
│   │   │   └── index.js
│   │   │
│   │   ├── assets/                   # 静态资源
│   │   ├── App.vue
│   │   └── main.js
│   │
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js            # TailwindCSS配置
│
└── start.bat                         # Windows启动脚本
```

---

## 3. 数据库设计

### 3.1 用户表 (users)

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户ID |
| username | VARCHAR(50) | UNIQUE NOT NULL | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 (bcrypt) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

### 3.2 平台配置表 (platform_configs)

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 配置ID |
| user_id | INTEGER | FK(users.id) NOT NULL | 用户ID |
| platform_code | VARCHAR(50) | NOT NULL | 平台代码 (houfaka/siyun) |
| shop_username | VARCHAR(100) | | 店铺账号 |
| shop_password | VARCHAR(255) | | 店铺密码 (加密存储) |
| product_urls | TEXT | | 商品链接 (JSON数组) |
| cookies | TEXT | | Cookie数据 (JSON) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

UNIQUE INDEX: (user_id, platform_code)

### 3.3 订单日志表 (order_logs)

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 日志ID |
| user_id | INTEGER | FK(users.id) NOT NULL | 用户ID |
| platform_code | VARCHAR(50) | NOT NULL | 平台代码 |
| product_url | VARCHAR(500) | | 商品链接 |
| original_price | DECIMAL(10,2) | | 原始价格 |
| new_price | DECIMAL(10,2) | | 修改价格 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态 (pending/processing/success/failed) |
| error_message | TEXT | | 错误信息 |
| qr_code_url | TEXT | | 二维码图片URL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 4. API设计

### 4.1 认证模块

#### POST /api/auth/register
**请求体**:
```json
{
  "username": "string (3-50字符)",
  "password": "string (6-100字符)"
}
```
**响应** (201):
```json
{
  "message": "注册成功",
  "user_id": 1
}
```

#### POST /api/auth/login
**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```
**响应** (200):
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "username": "string"
}
```

### 4.2 平台模块

#### GET /api/platforms
**响应** (200):
```json
{
  "platforms": [
    {
      "code": "houfaka",
      "name": "猴发卡",
      "host": "https://www.houfaka.com"
    },
    {
      "code": "siyun",
      "name": "四云发卡",
      "host": "https://shop.4yuns.com"
    }
  ]
}
```

#### POST /api/platforms/{platform_code}/login
**描述**: 登录平台店铺  
**请求体**:
```json
{
  "username": "店铺账号",
  "password": "店铺密码"
}
```
**响应** (200):
```json
{
  "success": true,
  "message": "登录成功",
  "shop_name": "店铺名称",
  "balance": 100.00
}
```

### 4.3 订单模块

#### POST /api/platforms/{platform_code}/price
**描述**: 获取商品价格  
**请求体**:
```json
{
  "product_url": "https://..."
}
```
**响应** (200):
```json
{
  "success": true,
  "product_id": "12345",
  "product_name": "商品名称",
  "original_price": 100.00,
  "stock": 999
}
```

#### POST /api/platforms/{platform_code}/order
**描述**: 提交订单并生成支付二维码  
**请求体**:
```json
{
  "product_url": "https://...",
  "new_price": 0.01
}
```
**响应** (200):
```json
{
  "success": true,
  "order_id": "ORD123",
  "qr_code_base64": "data:image/png;base64,...",
  "payment_url": "https://...",
  "logs": [
    "步骤1: 获取Cookie成功",
    "步骤2: 提交订单成功",
    "步骤3: 获取支付宝表单",
    "步骤4: 请求支付宝网关",
    "步骤5: 处理重定向",
    "步骤6: 生成二维码成功"
  ]
}
```

### 4.4 配置模块

#### GET /api/config/{platform_code}
**响应** (200):
```json
{
  "shop_username": "店铺账号",
  "product_urls": ["url1", "url2"],
  "has_login": true
}
```

#### PUT /api/config/{platform_code}
**请求体**:
```json
{
  "shop_username": "新账号",
  "product_urls": ["url1", "url2"]
}
```
**响应** (200):
```json
{
  "message": "配置保存成功"
}
```

---

## 5. 业务逻辑层设计

### 5.1 基础服务类 (BaseService)

```python
class BaseService:
    """基础服务类，提供通用方法"""
    
    def __init__(self, platform_code: str, host: str):
        self.platform_code = platform_code
        self.host = host
        self.session = requests.Session()
    
    def load_cookies(self, user_id: int) -> bool:
        """从数据库加载Cookie到session"""
        pass
    
    def save_cookies(self, user_id: int):
        """保存session Cookie到数据库"""
        pass
    
    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格（复用PC代码逻辑）"""
        pass
    
    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单（6步支付流程）"""
        pass
```

### 5.2 猴发卡服务 (HoufakaService)

继承BaseService，复用`auto_order.py`中的以下逻辑：
- 步骤1: 获取Cookie (`_step1_get_cookie`)
- 步骤2: 提交订单 (`_step2_submit_order`)
- 步骤3: 获取支付宝表单 (`_step3_get_alipay_form`)
- 步骤4: 请求支付宝网关 (`_step4_request_alipay`)
- 步骤5: 处理重定向 (`_step5_handle_redirect`)
- 步骤6: 生成二维码 (`_step6_generate_qrcode`)

### 5.3 四云发卡服务 (SiyunService)

继承BaseService，复用`auto_order_4yuns.py`中的逻辑：
- 与猴发卡相同，但包含额外的步骤2.5（指纹验证）
- 步骤3返回302重定向，需要步骤3.5处理

---

## 6. 前端设计

### 6.1 页面流程

```
登录页 → 控制台首页
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 平台管理   订单处理   系统设置
```

### 6.2 核心页面

#### 登录页 (Login.vue)
- 用户名/密码登录表单
- 注册链接跳转
- 登录成功后保存JWT到localStorage

#### 控制台 (Dashboard.vue)
- 显示可用平台列表
- 快速操作入口
- 最近订单记录

#### 平台管理 (PlatformManage.vue)
- 平台选择下拉框
- 店铺账号密码配置
- 商品链接管理
- 登录状态显示

#### 订单处理 (OrderProcess.vue)
- 选择平台
- 选择商品链接
- 输入新价格
- 点击"生成支付二维码"
- 显示处理进度（步骤日志）
- 显示生成的二维码

### 6.3 状态管理 (Pinia)

```javascript
// auth store
{
  token: string | null,
  username: string | null,
  login(token, username) { ... },
  logout() { ... }
}

// platform store
{
  currentPlatform: string | null,
  platforms: [],
  loginStatus: { loggedIn: false, shopName: '' },
  selectPlatform(code) { ... },
  loginShop(credentials) { ... }
}

// order store
{
  processing: false,
  logs: [],
  qrCode: null,
  processOrder(platform, url, price) { ... }
}
```

---

## 7. 安全设计

### 7.1 认证安全
- 密码使用bcrypt加密存储
- JWT token有效期24小时
- 敏感API需要Bearer Token认证

### 7.2 数据安全
- Cookie数据加密存储 (Fernet对称加密)
- SQL注入防护 (SQLAlchemy参数化查询)
- XSS防护 (前端输入转义)

### 7.3 通信安全
- 生产环境使用HTTPS
- CORS配置限制允许的源

---

## 8. 部署说明

### 8.1 后端启动

```bash
cd web/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8.2 前端构建

```bash
cd web/frontend
npm install
npm run build
```

### 8.3 生产部署

使用Nginx代理：
- 前端静态文件: `/` → `frontend/dist/`
- API请求: `/api` → `http://localhost:8000`

### 8.4 Windows启动脚本

```batch
@echo off
start "Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "Frontend" cmd /k "cd frontend && npm run dev"
```

---

## 9. 复用策略

### 9.1 直接复用的代码

| 源文件 | 复用内容 |
|--------|----------|
| `login.py` | 猴发卡登录逻辑、Cookie管理 |
| `login_4yuns.py` | 四云发卡登录逻辑 |
| `auto_order.py` | 猴发卡6步支付流程 |
| `auto_order_4yuns.py` | 四云发卡6步支付流程（含步骤2.5、3.5） |

### 9.2 需要改造的部分

| 原PC逻辑 | Web改造 |
|----------|---------|
| Tkinter日志回调 | 返回日志列表 |
| pickle持久化 | SQLite数据库存储 |
| 全局session | 用户隔离的session |
| 同步GUI阻塞 | FastAPI异步处理 |

### 9.3 不复用的部分

- Tkinter GUI代码
- PyInstaller打包配置
- 本地pickle文件读写

---

## 10. 开发阶段

### 阶段1: 后端基础
1. 创建FastAPI项目结构
2. 配置SQLite数据库
3. 实现用户认证模块
4. 实现基础API路由

### 阶段2: 业务逻辑
1. 创建BaseService基础类
2. 移植猴发卡业务逻辑
3. 移植四云发卡业务逻辑
4. 实现Cookie数据库持久化

### 阶段3: 前端基础
1. 创建Vue.js项目
2. 配置路由和状态管理
3. 实现登录/注册页面
4. 实现主布局框架

### 阶段4: 前端功能
1. 平台管理页面
2. 订单处理页面
3. 配置管理页面
4. API联调

### 阶段5: 测试与优化
1. 端到端测试
2. 错误处理优化
3. 性能优化
4. 部署文档

---

## 11. 依赖列表

### 后端 (requirements.txt)

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
requests>=2.31.0
beautifulsoup4>=4.12.0
qrcode[pil]>=7.4.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

### 前端 (package.json)

```json
{
  "dependencies": {
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.5.0",
    "element-plus": "^2.3.0",
    "@element-plus/icons-vue": "^2.1.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## 12. 错误处理

### 12.1 统一错误响应格式

```json
{
  "success": false,
  "error_code": "INVALID_CREDENTIALS",
  "message": "用户名或密码错误",
  "details": {}
}
```

### 12.2 错误码列表

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| INVALID_CREDENTIALS | 401 | 认证失败 |
| TOKEN_EXPIRED | 401 | Token过期 |
| PLATFORM_NOT_FOUND | 404 | 平台不存在 |
| LOGIN_FAILED | 400 | 店铺登录失败 |
| PRICE_FETCH_FAILED | 500 | 获取价格失败 |
| ORDER_FAILED | 500 | 订单处理失败 |
| CONFIG_SAVE_FAILED | 500 | 配置保存失败 |

---

## 13. 限制与假设

### 13.1 限制
- 不支持并发订单处理（单用户队列）
- 二维码以base64返回，不存储图片文件
- Cookie有效期由平台决定，需定期重新登录

### 13.2 假设
- 用户量<1000（SQLite适用）
- 直接部署在Windows/Linux服务器
- 网络可访问发卡平台和支付宝
