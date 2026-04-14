# GetPayurl Web

将PC桌面应用转换为Web版本的GetPayurl系统，支持猴发卡和四云发卡两个平台。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue.js 3 + Element Plus + Pinia
- **认证**: JWT

## 快速开始

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 启动应用

```bash
# Windows一键启动
start.bat

# 或手动启动
# 后端
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端
cd frontend
npm run dev
```

### 3. 访问应用

- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

## 功能特性

- 多用户认证系统
- 平台管理（猴发卡、四云发卡）
- 店铺账号登录
- 商品链接配置
- 商品价格查询
- 自动订单处理
- 支付二维码生成

## 项目结构

```
web/
├── backend/          # 后端FastAPI
│   └── app/
│       ├── routers/  # API路由
│       ├── services/ # 业务逻辑
│       └── utils/    # 工具函数
├── frontend/         # 前端Vue.js
│   └── src/
│       ├── views/    # 页面
│       ├── components/ # 组件
│       ├── api/      # API调用
│       └── stores/   # 状态管理
└── start.bat         # 启动脚本
```

## API文档

启动后端后访问 http://localhost:8000/docs 查看交互式API文档。

## 部署

### 生产环境构建

```bash
cd frontend
npm run build
```

使用Nginx代理：
- 静态文件: `frontend/dist/`
- API代理: `/api` → `http://localhost:8000`
