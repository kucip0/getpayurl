# GetPayurl Web版本实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将PC桌面应用（猴发卡和四云发卡）转换为Web版本，采用FastAPI + Vue.js 3前后端分离架构，支持多用户认证。

**Architecture:** 后端FastAPI提供REST API，复用现有Python业务逻辑；前端Vue.js 3 + Element Plus构建SPA；SQLite存储用户数据和配置。

**Tech Stack:** FastAPI, Vue.js 3, Element Plus, SQLAlchemy, SQLite, JWT, Pinia, Axios

---

## 文件结构总览

### 后端文件（按创建顺序）

| 文件 | 职责 | 创建阶段 |
|------|------|----------|
| `web/backend/requirements.txt` | Python依赖声明 | Task 1 |
| `web/backend/app/__init__.py` | 包初始化 | Task 1 |
| `web/backend/app/config.py` | 应用配置（JWT密钥、数据库路径） | Task 1 |
| `web/backend/app/database.py` | SQLite连接和表创建 | Task 1 |
| `web/backend/app/models.py` | SQLAlchemy数据模型 | Task 1 |
| `web/backend/app/schemas.py` | Pydantic请求/响应模型 | Task 2 |
| `web/backend/app/auth.py` | JWT认证工具（创建/验证Token） | Task 2 |
| `web/backend/app/dependencies.py` | 依赖注入（获取当前用户） | Task 2 |
| `web/backend/app/routers/auth.py` | 注册/登录API | Task 2 |
| `web/backend/app/main.py` | FastAPI应用入口 | Task 2 |
| `web/backend/app/utils/http_client.py` | HTTP会话管理工具 | Task 3 |
| `web/backend/app/utils/html_parser.py` | HTML解析工具 | Task 3 |
| `web/backend/app/utils/qr_generator.py` | 二维码生成工具 | Task 3 |
| `web/backend/app/services/base_service.py` | 基础服务类 | Task 4 |
| `web/backend/app/services/houfaka_service.py` | 猴发卡业务逻辑 | Task 5 |
| `web/backend/app/services/siyun_service.py` | 四云发卡业务逻辑 | Task 6 |
| `web/backend/app/routers/platforms.py` | 平台管理API | Task 7 |
| `web/backend/app/routers/orders.py` | 订单处理API | Task 7 |
| `web/backend/app/routers/config.py` | 配置管理API | Task 7 |

### 前端文件（按创建顺序）

| 文件 | 职责 | 创建阶段 |
|------|------|----------|
| `web/frontend/package.json` | Node.js依赖声明 | Task 8 |
| `web/frontend/vite.config.js` | Vite构建配置 | Task 8 |
| `web/frontend/index.html` | HTML入口 | Task 8 |
| `web/frontend/src/main.js` | Vue应用入口 | Task 8 |
| `web/frontend/src/App.vue` | 根组件 | Task 8 |
| `web/frontend/src/router/index.js` | 路由配置 | Task 8 |
| `web/frontend/src/api/index.js` | Axios实例配置 | Task 9 |
| `web/frontend/src/api/auth.js` | 认证API调用 | Task 9 |
| `web/frontend/src/api/platforms.js` | 平台API调用 | Task 9 |
| `web/frontend/src/api/orders.js` | 订单API调用 | Task 9 |
| `web/frontend/src/api/config.js` | 配置API调用 | Task 9 |
| `web/frontend/src/stores/auth.js` | 认证状态管理 | Task 10 |
| `web/frontend/src/stores/platform.js` | 平台状态管理 | Task 10 |
| `web/frontend/src/stores/order.js` | 订单状态管理 | Task 10 |
| `web/frontend/src/views/Login.vue` | 登录页 | Task 11 |
| `web/frontend/src/views/Register.vue` | 注册页 | Task 11 |
| `web/frontend/src/views/Dashboard.vue` | 控制台 | Task 12 |
| `web/frontend/src/views/PlatformManage.vue` | 平台管理页 | Task 13 |
| `web/frontend/src/views/OrderProcess.vue` | 订单处理页 | Task 14 |
| `web/frontend/src/components/PlatformSelector.vue` | 平台选择组件 | Task 13 |
| `web/frontend/src/components/QRCodeDisplay.vue` | 二维码显示组件 | Task 14 |
| `web/frontend/src/components/LogViewer.vue` | 日志查看组件 | Task 14 |
| `web/start.bat` | Windows启动脚本 | Task 15 |

---

## Task 1: 后端项目基础结构

**Files:**
- Create: `web/backend/requirements.txt`
- Create: `web/backend/app/__init__.py`
- Create: `web/backend/app/config.py`
- Create: `web/backend/app/database.py`
- Create: `web/backend/app/models.py`

- [ ] **Step 1: 创建项目目录和requirements.txt**

创建目录：
```bash
mkdir -p web/backend/app/routers
mkdir -p web/backend/app/services
mkdir -p web/backend/app/utils
mkdir -p web/frontend
```

`web/backend/requirements.txt`:
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
Pillow>=10.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

- [ ] **Step 2: 创建app/__init__.py**

```python
# GetPayurl Web Backend
```

- [ ] **Step 3: 创建app/config.py**

```python
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用
    APP_NAME: str = "GetPayurl Web"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 数据库
    DATABASE_URL: str = f"sqlite:///{Path(__file__).parent.parent / 'getpayurl.db'}"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 4: 创建app/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite需要
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 5: 创建app/models.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PlatformConfig(Base):
    """平台配置表"""
    __tablename__ = "platform_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform_code = Column(String(50), nullable=False, index=True)
    shop_username = Column(String(100))
    shop_password = Column(String(255))
    product_urls = Column(Text)  # JSON数组
    cookies = Column(Text)  # JSON
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OrderLog(Base):
    """订单日志表"""
    __tablename__ = "order_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform_code = Column(String(50), nullable=False)
    product_url = Column(String(500))
    original_price = Column(DECIMAL(10, 2))
    new_price = Column(DECIMAL(10, 2))
    status = Column(String(20), default="pending")  # pending/processing/success/failed
    error_message = Column(Text)
    qr_code_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 6: 验证数据库模型**

```bash
cd web/backend
python -c "from app.database import create_tables; create_tables(); print('数据库表创建成功')"
```

预期输出：`数据库表创建成功`

- [ ] **Step 7: Commit**

```bash
git add web/backend/
git commit -m "feat: 创建后端项目基础结构和数据库模型"
```

---

## Task 2: 用户认证模块

**Files:**
- Create: `web/backend/app/schemas.py`
- Create: `web/backend/app/auth.py`
- Create: `web/backend/app/dependencies.py`
- Create: `web/backend/app/routers/auth.py`
- Create: `web/backend/app/routers/__init__.py`
- Modify: `web/backend/app/main.py`

- [ ] **Step 1: 创建schemas.py**

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# 认证相关
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class RegisterResponse(BaseModel):
    message: str
    user_id: int


# 平台相关
class PlatformInfo(BaseModel):
    code: str
    name: str
    host: str


class PlatformListResponse(BaseModel):
    platforms: list[PlatformInfo]


class ShopLoginRequest(BaseModel):
    username: str
    password: str


class ShopLoginResponse(BaseModel):
    success: bool
    message: str
    shop_name: Optional[str] = None
    balance: Optional[float] = None


# 订单相关
class PriceRequest(BaseModel):
    product_url: str


class PriceResponse(BaseModel):
    success: bool
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    original_price: Optional[float] = None
    stock: Optional[int] = None


class OrderRequest(BaseModel):
    product_url: str
    new_price: float


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    qr_code_base64: Optional[str] = None
    payment_url: Optional[str] = None
    logs: list[str] = []


# 配置相关
class PlatformConfigResponse(BaseModel):
    shop_username: Optional[str] = None
    product_urls: list[str] = []
    has_login: bool = False


class PlatformConfigUpdate(BaseModel):
    shop_username: Optional[str] = None
    product_urls: list[str] = []
```

- [ ] **Step 2: 创建auth.py**

```python
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码JWT Token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

- [ ] **Step 3: 创建dependencies.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user
```

- [ ] **Step 4: 创建routers/__init__.py**

```python
# Routers package
```

- [ ] **Step 5: 创建routers/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, TokenResponse, RegisterResponse
from app.auth import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RegisterResponse(message="注册成功", user_id=new_user.id)


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 生成Token
    access_token = create_access_token(data={"sub": user.username})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username
    )
```

- [ ] **Step 6: 创建main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import auth

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)


@app.on_event("startup")
def on_startup():
    """应用启动时创建表"""
    create_tables()


@app.get("/")
def root():
    return {"message": "GetPayurl Web API", "version": "1.0.0"}
```

- [ ] **Step 7: 测试认证API**

```bash
cd web/backend
python -m uvicorn app.main:app --reload --port 8000
```

在另一个终端测试：
```bash
# 测试注册
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# 测试登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
```

- [ ] **Step 8: Commit**

```bash
git add web/backend/app/
git commit -m "feat: 实现用户认证模块（注册/登录/JWT）"
```

---

## Task 3: HTTP工具类

**Files:**
- Create: `web/backend/app/utils/__init__.py`
- Create: `web/backend/app/utils/http_client.py`
- Create: `web/backend/app/utils/html_parser.py`
- Create: `web/backend/app/utils/qr_generator.py`

- [ ] **Step 1: 创建utils/__init__.py**

```python
# Utils package
```

- [ ] **Step 2: 创建http_client.py**

```python
import os
from typing import Dict, Optional, Tuple

import requests


def create_session(verify_ssl: bool = False) -> requests.Session:
    """创建HTTP会话，配置浏览器伪装"""
    session = requests.Session()
    
    # 禁用SSL验证
    if not verify_ssl:
        session.verify = False
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        os.environ['CURL_CA_BUNDLE'] = ''
    
    # 浏览器请求头
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    
    return session


def extract_cookie_from_response(
    response: requests.Response,
    cookie_name: str
) -> Optional[str]:
    """从响应中提取指定Cookie值"""
    return response.cookies.get(cookie_name)
```

- [ ] **Step 3: 创建html_parser.py**

```python
import html as html_module
import re
from typing import Optional

from bs4 import BeautifulSoup


def unescape_html(html_content: str) -> str:
    """HTML反转义处理"""
    html_content = html_module.unescape(html_content)
    html_content = html_content.replace('\\/', '/')
    html_content = html_content.replace('\\"', '"')
    html_content = html_content.replace('\\n', '\n')
    html_content = html_content.replace('\\t', '\t')
    html_content = html_content.replace('\\\\', '\\')
    html_content = html_content.replace('&#x20;', ' ')
    return html_content


def extract_token_from_html(html: str, token_name: str = "__token__") -> Optional[str]:
    """从HTML中提取CSRF Token"""
    html = unescape_html(html)
    soup = BeautifulSoup(html, "html.parser")
    
    # 方法1: BeautifulSoup查找
    token_input = soup.find("input", {"name": token_name, "type": "hidden"})
    if token_input and token_input.get("value"):
        return token_input["value"]
    
    # 方法2: 正则表达式（5种模式）
    patterns = [
        rf'<input[^>]*name=["\']{token_name}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'<input[^>]*value=["\']([^"\']+)["\'][^>]*name=["\']{token_name}["\']',
        rf'name=["\']{token_name}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'<input[^>]*name=["\']{token_name}["\'][^>]*>',
        rf'<input[^>]*type=["\']hidden["\'][^>]*name=["\']{token_name}["\'][^>]*>',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            groups = match.groups()
            if groups:
                return groups[0]
            # 从完整标签中提取value
            tag_match = re.search(r'value=["\']([^"\']+)["\']', match.group(0))
            if tag_match:
                return tag_match.group(1)
    
    return None


def parse_form_data(form_element) -> dict:
    """解析表单数据为字典"""
    form_data = {}
    
    for input_elem in form_element.find_all(["input", "textarea", "select"]):
        name = input_elem.get("name")
        if not name:
            continue
        
        tag_type = input_elem.get("type", "text")
        
        if tag_type in ["hidden", "text", "number", "email"]:
            form_data[name] = input_elem.get("value", "")
        elif tag_type in ["radio", "checkbox"]:
            if input_elem.has_attr("checked"):
                form_data[name] = input_elem.get("value", "on")
        elif tag_type == "textarea":
            # 检查是否有Summernote编辑器
            summernote = input_elem.find_next_sibling("div", id=f"summernote-{name}")
            if summernote:
                form_data[name] = summernote.get_text()
            else:
                form_data[name] = input_elem.get_text()
        elif tag_type is None:  # select
            selected = input_elem.find("option", selected=True)
            if selected:
                form_data[name] = selected.get("value", "")
            elif input_elem.find("option"):
                form_data[name] = input_elem.find("option").get("value", "")
    
    return form_data
```

- [ ] **Step 4: 创建qr_generator.py**

```python
import base64
import io

import qrcode
from PIL import Image


def generate_qr_base64(url: str, size: int = 250) -> str:
    """生成二维码并返回base64编码"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size), Image.LANCZOS)
    
    # 转为base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"
```

- [ ] **Step 5: Commit**

```bash
git add web/backend/app/utils/
git commit -m "feat: 创建HTTP工具类（会话管理、HTML解析、二维码生成）"
```

---

## Task 4: 基础服务类

**Files:**
- Create: `web/backend/app/services/__init__.py`
- Create: `web/backend/app/services/base_service.py`
- Create: `web/backend/app/schemas.py` (添加ServiceResponse)

- [ ] **Step 1: 创建services/__init__.py**

```python
# Services package
```

- [ ] **Step 2: 更新schemas.py，添加ServiceResponse**

在文件末尾添加：

```python


# 服务响应
class ServiceResponse(BaseModel):
    """服务层统一响应"""
    success: bool
    message: str
    data: Optional[dict] = None
    logs: list[str] = []
```

- [ ] **Step 3: 创建base_service.py**

```python
import json
import uuid
from typing import Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from app.models import PlatformConfig
from app.utils.http_client import create_session
from app.utils.qr_generator import generate_qr_base64


class BaseService:
    """基础服务类"""
    
    PLATFORM_CODE: str = ""
    BASE_URL: str = ""
    TRACKING_COOKIE: str = ""
    FINGERPRINT_ENABLED: bool = False
    
    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.session = create_session(verify_ssl=False)
        self.fingerprint = str(uuid.uuid4())
        self.logs: List[str] = []
    
    def log(self, message: str):
        """添加日志"""
        self.logs.append(message)
    
    def load_cookies(self) -> bool:
        """从数据库加载Cookie"""
        config = self.db.query(PlatformConfig).filter(
            PlatformConfig.user_id == self.user_id,
            PlatformConfig.platform_code == self.PLATFORM_CODE
        ).first()
        
        if not config or not config.cookies:
            return False
        
        try:
            cookies = json.loads(config.cookies)
            for cookie in cookies:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain"),
                )
            return True
        except (json.JSONDecodeError, KeyError):
            return False
    
    def save_cookies(self):
        """保存Cookie到数据库"""
        config = self.db.query(PlatformConfig).filter(
            PlatformConfig.user_id == self.user_id,
            PlatformConfig.platform_code == self.PLATFORM_CODE
        ).first()
        
        if not config:
            return
        
        cookies_list = []
        for cookie in self.session.cookies:
            cookies_list.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
            })
        
        config.cookies = json.dumps(cookies_list)
        self.db.commit()
    
    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格（子类实现）"""
        raise NotImplementedError
    
    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单（子类实现）"""
        raise NotImplementedError
```

- [ ] **Step 4: Commit**

```bash
git add web/backend/app/services/base_service.py web/backend/app/schemas.py
git commit -m "feat: 创建基础服务类（Cookie管理、日志、会话）"
```

---

## Task 5: 猴发卡服务

**Files:**
- Create: `web/backend/app/services/houfaka_service.py`

- [ ] **Step 1: 创建houfaka_service.py**

从 `auto_order.py` 和 `login.py` 复制以下逻辑：

```python
import random
import re
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.html_parser import unescape_html, extract_token_from_html, parse_form_data


class HoufakaService(BaseService):
    """猴发卡服务"""
    
    PLATFORM_CODE = "houfaka"
    BASE_URL = "https://www.houfaka.com"
    TRACKING_COOKIE = "sc447eeeb"
    
    def login(self, username: str, password: str) -> dict:
        """登录猴发卡店铺"""
        try:
            # 1. 访问主页获取初始Cookie
            resp = self.session.get(f"{self.BASE_URL}/")
            resp.raise_for_status()
            
            # 2. 访问登录页提取token
            resp = self.session.get(f"{self.BASE_URL}/login")
            resp.raise_for_status()
            html = unescape_html(resp.text)
            
            token = extract_token_from_html(html)
            if not token:
                raise Exception("无法提取CSRF Token")
            
            # 3. POST登录
            login_data = {
                "__token__": token,
                "username": username,
                "password": password,
                "rememberme": "1",
            }
            
            resp = self.session.post(
                f"{self.BASE_URL}/index/user/doLogin",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"登录失败: {result.get('msg', '未知错误')}")
            
            # 4. 验证merchant Cookie
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                raise Exception("登录失败: merchant Cookie不存在")
            
            self.log("登录成功")
            return {
                "success": True,
                "message": "登录成功",
                "shop_name": username,
            }
            
        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise
    
    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格"""
        try:
            # 使用merchant_session（已登录）获取商品页面
            resp = self.session.get(product_url)
            resp.raise_for_status()
            
            html = unescape_html(resp.text)
            soup = BeautifulSoup(html, "html.parser")
            
            # 提取商品参数
            params = {}
            for input_elem in soup.find_all("input", attrs={"name": True}):
                name = input_elem["name"]
                value = input_elem.get("value", "")
                params[name] = value
            
            # 填充默认值
            params.setdefault("feePayer", "2")
            params.setdefault("fee_rate", "0.05")
            params.setdefault("min_fee", "0.1")
            params.setdefault("rate", "100")
            params.setdefault("is_contact_limit", "default")
            params.setdefault("limit_quantity", "1")
            params.setdefault("cardNoLength", "0")
            params.setdefault("cardPwdLength", "0")
            params.setdefault("is_discount", "0")
            params.setdefault("coupon_ctype", "0")
            params.setdefault("coupon_value", "0")
            params.setdefault("sms_price", "0")
            
            return {
                "success": True,
                "product_id": params.get("goodid"),
                "product_name": params.get("goods_name", "未知商品"),
                "original_price": float(params.get("price", 0)),
                "stock": int(params.get("kucun", 0)),
            }
            
        except Exception as e:
            self.log(f"获取商品价格失败: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单并生成支付二维码"""
        self.logs = []
        
        try:
            # 步骤1: 获取Cookie和参数
            cookie, params = self._step1_get_cookie_and_params(product_url)
            
            # 计算新价格
            paymoney = round(float(new_price) * 1 * (1 + 0.05), 2)
            params["price"] = str(new_price)
            params["paymoney"] = str(paymoney)
            
            # 步骤2: 提交订单
            trade_no = self._step2_submit_order(cookie, params)
            
            # 步骤3: 获取支付宝表单
            alipay_params = self._step3_get_alipay_form(cookie, trade_no)
            
            # 步骤4: 请求支付宝网关
            location1, alipay_cookies = self._step4_request_alipay_gateway(alipay_params)
            
            # 步骤5: 跟随重定向
            final_url = self._step5_follow_redirect(location1, alipay_cookies)
            
            # 步骤6: 生成二维码
            qr_base64 = self._step6_generate_qrcode(final_url)
            
            return {
                "success": True,
                "order_id": trade_no,
                "qr_code_base64": qr_base64,
                "payment_url": final_url,
                "logs": self.logs,
            }
            
        except Exception as e:
            self.log(f"订单处理失败: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "logs": self.logs,
            }
    
    def _step1_get_cookie_and_params(self, url: str) -> Tuple[str, dict]:
        """步骤1: 获取Cookie和商品参数"""
        resp = self.session.get(url)
        resp.raise_for_status()
        
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        
        # 提取Cookie
        cookie = self.session.cookies.get(self.TRACKING_COOKIE)
        if not cookie:
            cookie = resp.cookies.get(self.TRACKING_COOKIE)
        
        # 提取参数
        params = {}
        for input_elem in soup.find_all("input", attrs={"name": True}):
            name = input_elem["name"]
            value = input_elem.get("value", "")
            params[name] = value
        
        # 填充默认值
        defaults = {
            "feePayer": "2", "fee_rate": "0.05", "min_fee": "0.1",
            "rate": "100", "is_contact_limit": "default",
            "limit_quantity": "1", "cardNoLength": "0",
            "cardPwdLength": "0", "is_discount": "0",
            "coupon_ctype": "0", "coupon_value": "0",
            "sms_price": "0", "is_pwdforsearch": "",
            "is_coupon": "", "select_cards": ""
        }
        for key, value in defaults.items():
            params.setdefault(key, value)
        
        self.log("步骤1: 获取Cookie和商品参数成功")
        return cookie, params
    
    def _step2_submit_order(self, cookie: str, params: dict) -> str:
        """步骤2: 提交订单"""
        # 生成随机手机号
        contact = f"1{random.randint(3,9)}{''.join([str(random.randint(0,9)) for _ in range(9)])}"
        
        order_data = {
            "goodid": params.get("goodid"),
            "cateid": params.get("cateid"),
            "quantity": "1",
            "contact": contact,
            "email": f"{contact}@example.com",
            "couponcode": "",
            "pwdforsearch1": "",
            "pwdforsearch2": "",
            "is_contact_limit": params.get("is_contact_limit"),
            "limit_quantity": params.get("limit_quantity"),
            "userid": params.get("userid"),
            "token": params.get("token"),
            "cardNoLength": params.get("cardNoLength"),
            "cardPwdLength": params.get("cardPwdLength"),
            "is_discount": params.get("is_discount"),
            "coupon_ctype": params.get("coupon_ctype"),
            "coupon_value": params.get("coupon_value"),
            "sms_price": params.get("sms_price"),
            "paymoney": params.get("paymoney"),
            "danjia": params.get("danjia"),
            "is_pwdforsearch": params.get("is_pwdforsearch"),
            "is_coupon": params.get("is_coupon"),
            "price": params.get("price"),
            "kucun": params.get("kucun"),
            "select_cards": params.get("select_cards"),
            "feePayer": params.get("feePayer"),
            "fee_rate": params.get("fee_rate"),
            "min_fee": params.get("min_fee"),
            "rate": params.get("rate"),
            "pid": "2",  # 支付宝
        }
        
        resp = self.session.post(
            f"{self.BASE_URL}/pay/order",
            data=order_data,
            headers={
                "Referer": f"{self.BASE_URL}/details/{params.get('goodid')}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        resp.raise_for_status()
        
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        
        trade_no_input = soup.find("input", attrs={"name": "trade_no"})
        if not trade_no_input or not trade_no_input.get("value"):
            raise Exception("未找到trade_no")
        
        trade_no = trade_no_input["value"]
        self.log("步骤2: 提交订单成功")
        return trade_no
    
    def _step3_get_alipay_form(self, cookie: str, orderid: str) -> dict:
        """步骤3: 获取支付宝表单"""
        resp = self.session.get(
            f"{self.BASE_URL}/index/pay/payment",
            params={"trade_no": orderid, "agree": "on"}
        )
        resp.raise_for_status()
        
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        
        form = soup.find("form", id="alipaysubmit")
        if not form:
            raise Exception("未找到支付宝表单")
        
        alipay_params = {}
        for input_elem in form.find_all("input", attrs={"type": "hidden"}):
            name = input_elem.get("name")
            value = input_elem.get("value")
            if name and value:
                alipay_params[name] = value
        
        self.log("步骤3: 获取支付宝表单成功")
        return alipay_params
    
    def _step4_request_alipay_gateway(self, alipay_params: dict) -> Tuple[str, dict]:
        """步骤4: 请求支付宝网关"""
        # 参数排序
        param_order = [
            "app_id", "method", "format", "return_url", "charset",
            "sign_type", "timestamp", "version", "notify_url",
            "biz_content", "sign",
        ]
        
        sorted_params = {}
        for key in param_order:
            if key in alipay_params:
                sorted_params[key] = alipay_params[key]
        
        # 覆盖必要参数
        sorted_params["method"] = "alipay.trade.wap.pay"
        sorted_params["charset"] = "utf-8"
        
        # 修改biz_content
        import json
        biz_content = json.loads(sorted_params.get("biz_content", "{}"))
        biz_content["product_code"] = "QUICK_WAP_WAY"
        sorted_params["biz_content"] = json.dumps(biz_content, ensure_ascii=True)
        
        resp = self.session.post(
            "https://openapi.alipay.com/gateway.do?charset=utf-8",
            data=sorted_params,
            allow_redirects=False
        )
        
        if resp.status_code not in [301, 302]:
            raise Exception(f"支付宝网关返回非重定向: {resp.status_code}")
        
        location = resp.headers.get("Location")
        if not location:
            raise Exception("未找到重定向地址")
        
        alipay_cookies = dict(resp.cookies)
        self.log("步骤4: 请求支付宝网关成功")
        return location, alipay_cookies
    
    def _step5_follow_redirect(self, location: str, alipay_cookies: dict) -> str:
        """步骤5: 跟随重定向"""
        # 合并Cookie
        all_cookies = {}
        for k, v in self.session.cookies.items():
            all_cookies[k] = v
        for k, v in alipay_cookies.items():
            all_cookies[k] = v
        
        resp = self.session.get(
            location,
            cookies=all_cookies,
            allow_redirects=False
        )
        
        if resp.status_code in [301, 302]:
            final_url = resp.headers.get("Location", resp.url)
        else:
            final_url = resp.url
        
        self.log("步骤5: 跟随重定向成功")
        return final_url
    
    def _step6_generate_qrcode(self, url: str) -> str:
        """步骤6: 生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("步骤6: 生成二维码成功")
        return qr_base64
```

- [ ] **Step 2: Commit**

```bash
git add web/backend/app/services/houfaka_service.py
git commit -m "feat: 实现猴发卡业务逻辑（6步支付流程）"
```

---

## Task 6: 四云发卡服务

**Files:**
- Create: `web/backend/app/services/siyun_service.py`

- [ ] **Step 1: 创建siyun_service.py**

从 `auto_order_4yuns.py` 和 `login_4yuns.py` 复制，注意差异：
- Cookie名称: `s1c9ae71b`
- 步骤2.5指纹验证
- 步骤3返回302重定向
- 步骤3.5处理重定向
- notify_url不同

```python
import json
import random
from typing import Tuple

from bs4 import BeautifulSoup

from app.services.base_service import BaseService
from app.utils.html_parser import unescape_html


class SiyunService(BaseService):
    """四云发卡服务"""
    
    PLATFORM_CODE = "siyun"
    BASE_URL = "https://shop.4yuns.com"
    TRACKING_COOKIE = "s1c9ae71b"
    FINGERPRINT_ENABLED = True
    
    def login(self, username: str, password: str) -> dict:
        """登录四云发卡店铺"""
        try:
            # 1. 访问主页
            resp = self.session.get(f"{self.BASE_URL}/")
            resp.raise_for_status()
            
            # 2. 访问登录页提取token
            resp = self.session.get(f"{self.BASE_URL}/login")
            resp.raise_for_status()
            html = unescape_html(resp.text)
            
            from app.utils.html_parser import extract_token_from_html
            token = extract_token_from_html(html)
            if not token:
                raise Exception("无法提取CSRF Token")
            
            # 3. POST登录
            login_data = {
                "__token__": token,
                "username": username,
                "password": password,
                "rememberme": "1",
            }
            
            resp = self.session.post(
                f"{self.BASE_URL}/index/user/doLogin",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 1:
                raise Exception(f"登录失败: {result.get('msg', '未知错误')}")
            
            merchant_cookie = self.session.cookies.get("merchant")
            if not merchant_cookie:
                raise Exception("登录失败: merchant Cookie不存在")
            
            self.log("登录成功")
            return {"success": True, "message": "登录成功", "shop_name": username}
            
        except Exception as e:
            self.log(f"登录失败: {str(e)}")
            raise
    
    def get_product_price(self, product_url: str) -> dict:
        """获取商品价格"""
        try:
            # 四云需要临时修改Accept头避免JSON编码
            original_accept = self.session.headers.get("Accept")
            self.session.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            
            resp = self.session.get(product_url)
            resp.raise_for_status()
            
            # 恢复Accept头
            if original_accept:
                self.session.headers["Accept"] = original_accept
            
            html = unescape_html(resp.text)
            soup = BeautifulSoup(html, "html.parser")
            
            params = {}
            for input_elem in soup.find_all("input", attrs={"name": True}):
                name = input_elem["name"]
                value = input_elem.get("value", "")
                params[name] = value
            
            params.setdefault("feePayer", "2")
            params.setdefault("fee_rate", "0.05")
            params.setdefault("min_fee", "0.1")
            params.setdefault("rate", "100")
            
            return {
                "success": True,
                "product_id": params.get("goodid"),
                "product_name": params.get("goods_name", "未知商品"),
                "original_price": float(params.get("price", 0)),
                "stock": int(params.get("kucun", 0)),
            }
            
        except Exception as e:
            self.log(f"获取商品价格失败: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def submit_order(self, product_url: str, new_price: float) -> dict:
        """提交订单（包含步骤2.5和3.5）"""
        self.logs = []
        
        try:
            # 步骤1
            cookie, params = self._step1_get_cookie_and_params(product_url)
            
            paymoney = round(float(new_price) * 1 * (1 + 0.05), 2)
            params["price"] = str(new_price)
            params["paymoney"] = str(paymoney)
            
            # 步骤2
            trade_no = self._step2_submit_order(cookie, params)
            
            # 步骤2.5: 指纹验证（四云特有）
            self._step25_check_buyer(trade_no)
            
            # 步骤3: 返回重定向地址
            redirect_url = self._step3_get_alipay_form(cookie, trade_no)
            
            # 步骤3.5: 处理重定向（四云特有）
            alipay_params = self._step35_get_alipay_form_from_redirect(redirect_url, cookie)
            
            # 步骤4
            location1, alipay_cookies = self._step4_request_alipay_gateway(alipay_params)
            
            # 步骤5
            final_url = self._step5_follow_redirect(location1, alipay_cookies)
            
            # 步骤6
            qr_base64 = self._step6_generate_qrcode(final_url)
            
            return {
                "success": True,
                "order_id": trade_no,
                "qr_code_base64": qr_base64,
                "payment_url": final_url,
                "logs": self.logs,
            }
            
        except Exception as e:
            self.log(f"订单处理失败: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "logs": self.logs,
            }
    
    def _step1_get_cookie_and_params(self, url: str) -> Tuple[str, dict]:
        """步骤1: 获取Cookie（清除其他Cookie）"""
        # 清除所有Cookie，只保留s1c9ae71b
        self.session.cookies.clear()
        
        resp = self.session.get(url)
        resp.raise_for_status()
        
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        
        cookie = self.session.cookies.get(self.TRACKING_COOKIE)
        
        params = {}
        for input_elem in soup.find_all("input", attrs={"name": True}):
            name = input_elem["name"]
            value = input_elem.get("value", "")
            params[name] = value
        
        defaults = {
            "feePayer": "2", "fee_rate": "0.05", "min_fee": "0.1",
            "rate": "100", "is_contact_limit": "default",
            "limit_quantity": "1", "cardNoLength": "0",
            "cardPwdLength": "0", "is_discount": "0",
            "coupon_ctype": "0", "coupon_value": "0",
            "sms_price": "0"
        }
        for key, value in defaults.items():
            params.setdefault(key, value)
        
        self.log("步骤1: 获取Cookie和商品参数成功")
        return cookie, params
    
    def _step2_submit_order(self, cookie: str, params: dict) -> str:
        """步骤2: 提交订单（使用完整请求头）"""
        contact = f"1{random.randint(3,9)}{''.join([str(random.randint(0,9)) for _ in range(9)])}"
        
        order_data = {
            "goodid": params.get("goodid"),
            "cateid": params.get("cateid"),
            "quantity": "1",
            "contact": contact,
            "email": f"{contact}@example.com",
            "couponcode": "",
            "pwdforsearch1": "",
            "pwdforsearch2": "",
            "is_contact_limit": params.get("is_contact_limit"),
            "limit_quantity": params.get("limit_quantity"),
            "userid": params.get("userid"),
            "token": params.get("token"),
            "cardNoLength": params.get("cardNoLength"),
            "cardPwdLength": params.get("cardPwdLength"),
            "is_discount": params.get("is_discount"),
            "coupon_ctype": params.get("coupon_ctype"),
            "coupon_value": params.get("coupon_value"),
            "sms_price": params.get("sms_price"),
            "paymoney": params.get("paymoney"),
            "danjia": params.get("danjia"),
            "is_pwdforsearch": params.get("is_pwdforsearch"),
            "is_coupon": params.get("is_coupon"),
            "price": params.get("price"),
            "kucun": params.get("kucun"),
            "select_cards": params.get("select_cards"),
            "feePayer": params.get("feePayer"),
            "fee_rate": params.get("fee_rate"),
            "min_fee": params.get("min_fee"),
            "rate": params.get("rate"),
            "pid": "2",
        }
        
        resp = self.session.post(
            f"{self.BASE_URL}/pay/order",
            data=order_data,
            headers={
                "Referer": url,  # 使用商品详情页作为Referer
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        resp.raise_for_status()
        
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        
        trade_no_input = soup.find("input", attrs={"name": "trade_no"})
        if not trade_no_input or not trade_no_input.get("value"):
            raise Exception("未找到trade_no")
        
        trade_no = trade_no_input["value"]
        self.log("步骤2: 提交订单成功")
        return trade_no
    
    def _step25_check_buyer(self, orderid: str):
        """步骤2.5: 验证设备指纹"""
        check_data = {
            "trade_no": orderid,
            "fingerprint": self.fingerprint,
            "wxauth": "",
        }
        
        resp = self.session.post(
            f"{self.BASE_URL}/index/pay/check_buyer",
            json=check_data
        )
        resp.raise_for_status()
        result = resp.json()
        
        if result.get("status") == "tip":
            raise Exception(f"指纹验证失败: {result.get('msg')}")
        
        self.log("步骤2.5: 指纹验证成功")
    
    def _step3_get_alipay_form(self, cookie: str, orderid: str) -> str:
        """步骤3: 获取重定向地址"""
        resp = self.session.get(
            f"{self.BASE_URL}/index/pay/payment",
            params={"trade_no": orderid, "agree": "on"},
            allow_redirects=False
        )
        
        if resp.status_code in [301, 302]:
            redirect_url = resp.headers.get("Location")
            if not redirect_url:
                raise Exception("未找到重定向地址")
            self.log("步骤3: 获取重定向地址成功")
            return redirect_url
        else:
            raise Exception(f"步骤3返回非重定向状态: {resp.status_code}")
    
    def _step35_get_alipay_form_from_redirect(self, redirect_url: str, cookie: str) -> dict:
        """步骤3.5: 请求重定向地址获取支付宝表单"""
        resp = self.session.get(redirect_url)
        resp.raise_for_status()
        
        html = unescape_html(resp.text)
        soup = BeautifulSoup(html, "html.parser")
        
        form = soup.find("form", id="alipaysubmit")
        if not form:
            raise Exception("未找到支付宝表单")
        
        alipay_params = {}
        for input_elem in form.find_all("input", attrs={"type": "hidden"}):
            name = input_elem.get("name")
            value = input_elem.get("value")
            if name and value:
                alipay_params[name] = value
        
        self.log("步骤3.5: 获取支付宝表单成功")
        return alipay_params
    
    def _step4_request_alipay_gateway(self, alipay_params: dict) -> Tuple[str, dict]:
        """步骤4: 请求支付宝网关"""
        param_order = [
            "app_id", "method", "format", "return_url", "charset",
            "sign_type", "timestamp", "version", "notify_url",
            "biz_content", "sign",
        ]
        
        sorted_params = {}
        for key in param_order:
            if key in alipay_params:
                sorted_params[key] = alipay_params[key]
        
        sorted_params["method"] = "alipay.trade.wap.pay"
        sorted_params["charset"] = "utf-8"
        
        # 四云特有的notify_url
        sorted_params["notify_url"] = "http://not.pay.4yun.4yuns.com/pay/Alipay_Wap/notify"
        
        import json as json_module
        biz_content = json_module.loads(sorted_params.get("biz_content", "{}"))
        biz_content["product_code"] = "QUICK_WAP_WAY"
        sorted_params["biz_content"] = json_module.dumps(biz_content, ensure_ascii=True)
        
        resp = self.session.post(
            "https://openapi.alipay.com/gateway.do?charset=utf-8",
            data=sorted_params,
            allow_redirects=False
        )
        
        if resp.status_code not in [301, 302]:
            raise Exception(f"支付宝网关返回非重定向: {resp.status_code}")
        
        location = resp.headers.get("Location")
        if not location:
            raise Exception("未找到重定向地址")
        
        alipay_cookies = dict(resp.cookies)
        self.log("步骤4: 请求支付宝网关成功")
        return location, alipay_cookies
    
    def _step5_follow_redirect(self, location: str, alipay_cookies: dict) -> str:
        """步骤5: 跟随重定向"""
        all_cookies = {}
        for k, v in self.session.cookies.items():
            all_cookies[k] = v
        for k, v in alipay_cookies.items():
            all_cookies[k] = v
        
        resp = self.session.get(
            location,
            cookies=all_cookies,
            allow_redirects=False
        )
        
        if resp.status_code in [301, 302]:
            final_url = resp.headers.get("Location", resp.url)
        else:
            final_url = resp.url
        
        self.log("步骤5: 跟随重定向成功")
        return final_url
    
    def _step6_generate_qrcode(self, url: str) -> str:
        """步骤6: 生成二维码"""
        from app.utils.qr_generator import generate_qr_base64
        qr_base64 = generate_qr_base64(url)
        self.log("步骤6: 生成二维码成功")
        return qr_base64
```

- [ ] **Step 2: Commit**

```bash
git add web/backend/app/services/siyun_service.py
git commit -m "feat: 实现四云发卡业务逻辑（含步骤2.5和3.5）"
```

---

## Task 7: 平台、订单、配置API

**Files:**
- Create: `web/backend/app/routers/platforms.py`
- Create: `web/backend/app/routers/orders.py`
- Create: `web/backend/app/routers/config.py`
- Modify: `web/backend/app/main.py`

- [ ] **Step 1: 创建platforms.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, PlatformConfig
from app.schemas import (
    PlatformInfo, PlatformListResponse,
    ShopLoginRequest, ShopLoginResponse
)
from app.services.houfaka_service import HoufakaService
from app.services.siyun_service import SiyunService

router = APIRouter(prefix="/api/platforms", tags=["平台"])

PLATFORMS = [
    PlatformInfo(code="houfaka", name="猴发卡", host="https://www.houfaka.com"),
    PlatformInfo(code="siyun", name="四云发卡", host="https://shop.4yuns.com"),
]


def get_service(platform_code: str, user_id: int, db: Session):
    """获取平台服务实例"""
    if platform_code == "houfaka":
        return HoufakaService(user_id, db)
    elif platform_code == "siyun":
        return SiyunService(user_id, db)
    else:
        raise HTTPException(status_code=404, detail="平台不存在")


@router.get("", response_model=PlatformListResponse)
def list_platforms(current_user: User = Depends(get_current_user)):
    """获取平台列表"""
    return PlatformListResponse(platforms=PLATFORMS)


@router.post("/{platform_code}/login", response_model=ShopLoginResponse)
def shop_login(
    platform_code: str,
    login_data: ShopLoginRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """店铺登录"""
    service = get_service(platform_code, current_user.id, db)
    
    # 保存配置
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()
    
    if not config:
        config = PlatformConfig(
            user_id=current_user.id,
            platform_code=platform_code,
            shop_username=login_data.username,
            shop_password=login_data.password,
        )
        db.add(config)
    else:
        config.shop_username = login_data.username
        config.shop_password = login_data.password
    
    db.commit()
    
    try:
        result = service.login(login_data.username, login_data.password)
        service.save_cookies()
        return ShopLoginResponse(
            success=True,
            message=result["message"],
            shop_name=result.get("shop_name"),
        )
    except Exception as e:
        return ShopLoginResponse(
            success=False,
            message=str(e)
        )
```

- [ ] **Step 2: 创建orders.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, OrderLog
from app.schemas import PriceRequest, PriceResponse, OrderRequest, OrderResponse
from app.routers.platforms import get_service

router = APIRouter(prefix="/api/platforms", tags=["订单"])


@router.post("/{platform_code}/price", response_model=PriceResponse)
def get_price(
    platform_code: str,
    request: PriceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取商品价格"""
    service = get_service(platform_code, current_user.id, db)
    service.load_cookies()
    
    result = service.get_product_price(request.product_url)
    return PriceResponse(**result)


@router.post("/{platform_code}/order", response_model=OrderResponse)
def submit_order(
    platform_code: str,
    request: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交订单并生成二维码"""
    service = get_service(platform_code, current_user.id, db)
    service.load_cookies()
    
    result = service.submit_order(request.product_url, request.new_price)
    
    # 记录订单日志
    order_log = OrderLog(
        user_id=current_user.id,
        platform_code=platform_code,
        product_url=request.product_url,
        new_price=request.new_price,
        status="success" if result["success"] else "failed",
        error_message=result.get("error_message"),
        qr_code_url=result.get("payment_url"),
    )
    db.add(order_log)
    db.commit()
    
    return OrderResponse(**result)
```

- [ ] **Step 3: 创建config.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, PlatformConfig
from app.schemas import PlatformConfigResponse, PlatformConfigUpdate

router = APIRouter(prefix="/api/config", tags=["配置"])


@router.get("/{platform_code}", response_model=PlatformConfigResponse)
def get_config(
    platform_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取平台配置"""
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()
    
    if not config:
        return PlatformConfigResponse()
    
    product_urls = []
    if config.product_urls:
        try:
            product_urls = json.loads(config.product_urls)
        except json.JSONDecodeError:
            product_urls = []
    
    return PlatformConfigResponse(
        shop_username=config.shop_username,
        product_urls=product_urls,
        has_login=bool(config.shop_username and config.shop_password),
    )


@router.put("/{platform_code}")
def update_config(
    platform_code: str,
    update_data: PlatformConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新平台配置"""
    config = db.query(PlatformConfig).filter(
        PlatformConfig.user_id == current_user.id,
        PlatformConfig.platform_code == platform_code
    ).first()
    
    if not config:
        config = PlatformConfig(
            user_id=current_user.id,
            platform_code=platform_code,
        )
        db.add(config)
    
    if update_data.shop_username is not None:
        config.shop_username = update_data.shop_username
    
    config.product_urls = json.dumps(update_data.product_urls)
    db.commit()
    
    return {"message": "配置保存成功"}
```

- [ ] **Step 4: 更新main.py注册所有路由**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import auth, platforms, orders, config

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(orders.router)
app.include_router(config.router)


@app.on_event("startup")
def on_startup():
    create_tables()


@app.get("/")
def root():
    return {"message": "GetPayurl Web API", "version": "1.0.0"}
```

- [ ] **Step 5: Commit**

```bash
git add web/backend/app/routers/ web/backend/app/main.py
git commit -m "feat: 实现平台、订单、配置API"
```

---

## Task 8: 前端项目初始化

**Files:**
- Create: `web/frontend/package.json`
- Create: `web/frontend/vite.config.js`
- Create: `web/frontend/index.html`
- Create: `web/frontend/src/main.js`
- Create: `web/frontend/src/App.vue`
- Create: `web/frontend/src/router/index.js`
- Create: `web/frontend/tailwind.config.js`
- Create: `web/frontend/postcss.config.js`

- [ ] **Step 1: 创建package.json**

```json
{
  "name": "getpayurl-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
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

- [ ] **Step 2: 创建vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

- [ ] **Step 3: 创建index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GetPayurl Web</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: 创建src/main.js**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

- [ ] **Step 5: 创建src/App.vue**

```vue
<template>
  <router-view />
</template>

<script setup>
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
```

- [ ] **Step 6: 创建src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/platform',
    name: 'PlatformManage',
    component: () => import('../views/PlatformManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/order',
    name: 'OrderProcess',
    component: () => import('../views/OrderProcess.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 7: 创建tailwind.config.js**

```javascript
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 8: 创建postcss.config.js**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 9: 安装依赖并测试**

```bash
cd web/frontend
npm install
npm run dev
```

访问 http://localhost:5173 确认前端正常加载

- [ ] **Step 10: Commit**

```bash
git add web/frontend/
git commit -m "feat: 初始化Vue.js前端项目"
```

---

## Task 9: 前端API层

**Files:**
- Create: `web/frontend/src/api/index.js`
- Create: `web/frontend/src/api/auth.js`
- Create: `web/frontend/src/api/platforms.js`
- Create: `web/frontend/src/api/orders.js`
- Create: `web/frontend/src/api/config.js`

- [ ] **Step 1: 创建api/index.js（Axios实例）**

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    }
    return Promise.reject(error)
  }
)

export default api
```

- [ ] **Step 2: 创建api/auth.js**

```javascript
import api from './index'

export const register = (username, password) => {
  return api.post('/auth/register', { username, password })
}

export const login = (username, password) => {
  return api.post('/auth/login', { username, password })
}
```

- [ ] **Step 3: 创建api/platforms.js**

```javascript
import api from './index'

export const getPlatforms = () => {
  return api.get('/platforms')
}

export const shopLogin = (platformCode, username, password) => {
  return api.post(`/platforms/${platformCode}/login`, {
    username,
    password,
  })
}

export const getPrice = (platformCode, productUrl) => {
  return api.post(`/platforms/${platformCode}/price`, {
    product_url: productUrl,
  })
}

export const submitOrder = (platformCode, productUrl, newPrice) => {
  return api.post(`/platforms/${platformCode}/order`, {
    product_url: productUrl,
    new_price: newPrice,
  })
}
```

- [ ] **Step 4: 创建api/config.js**

```javascript
import api from './index'

export const getConfig = (platformCode) => {
  return api.get(`/config/${platformCode}`)
}

export const updateConfig = (platformCode, data) => {
  return api.put(`/config/${platformCode}`, data)
}
```

- [ ] **Step 5: Commit**

```bash
git add web/frontend/src/api/
git commit -m "feat: 创建前端API层"
```

---

## Task 10: 前端状态管理

**Files:**
- Create: `web/frontend/src/stores/auth.js`
- Create: `web/frontend/src/stores/platform.js`
- Create: `web/frontend/src/stores/order.js`

- [ ] **Step 1: 创建stores/auth.js**

```javascript
import { defineStore } from 'pinia'
import { login as apiLogin } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    username: localStorage.getItem('username') || null,
  }),
  
  actions: {
    async login(username, password) {
      const response = await apiLogin(username, password)
      this.token = response.data.access_token
      this.username = response.data.username
      
      localStorage.setItem('token', this.token)
      localStorage.setItem('username', this.username)
    },
    
    logout() {
      this.token = null
      this.username = null
      localStorage.removeItem('token')
      localStorage.removeItem('username')
    }
  }
})
```

- [ ] **Step 2: 创建stores/platform.js**

```javascript
import { defineStore } from 'pinia'
import { getPlatforms, shopLogin as apiShopLogin } from '../api/platforms'
import { getConfig, updateConfig as apiUpdateConfig } from '../api/config'

export const usePlatformStore = defineStore('platform', {
  state: () => ({
    platforms: [],
    currentPlatform: null,
    loginStatus: {
      loggedIn: false,
      shopName: '',
    },
    config: {
      shop_username: '',
      product_urls: [],
      has_login: false,
    }
  }),
  
  actions: {
    async loadPlatforms() {
      const response = await getPlatforms()
      this.platforms = response.data.platforms
    },
    
    async loadConfig(platformCode) {
      const response = await getConfig(platformCode)
      this.config = response.data
    },
    
    async updateConfig(platformCode, data) {
      await apiUpdateConfig(platformCode, data)
      await this.loadConfig(platformCode)
    },
    
    async shopLogin(platformCode, username, password) {
      const response = await apiShopLogin(platformCode, username, password)
      this.loginStatus = {
        loggedIn: response.data.success,
        shopName: response.data.shop_name || '',
      }
      return response.data
    }
  }
})
```

- [ ] **Step 3: 创建stores/order.js**

```javascript
import { defineStore } from 'pinia'
import { getPrice as apiGetPrice, submitOrder as apiSubmitOrder } from '../api/platforms'

export const useOrderStore = defineStore('order', {
  state: () => ({
    processing: false,
    logs: [],
    qrCode: null,
    paymentUrl: null,
    priceInfo: null,
  }),
  
  actions: {
    async getPrice(platformCode, productUrl) {
      const response = await apiGetPrice(platformCode, productUrl)
      this.priceInfo = response.data
      return response.data
    },
    
    async processOrder(platformCode, productUrl, newPrice) {
      this.processing = true
      this.logs = []
      this.qrCode = null
      this.paymentUrl = null
      
      try {
        const response = await apiSubmitOrder(platformCode, productUrl, newPrice)
        this.logs = response.data.logs || []
        
        if (response.data.success) {
          this.qrCode = response.data.qr_code_base64
          this.paymentUrl = response.data.payment_url
        }
        
        return response.data
      } finally {
        this.processing = false
      }
    }
  }
})
```

- [ ] **Step 4: Commit**

```bash
git add web/frontend/src/stores/
git commit -m "feat: 创建前端状态管理"
```

---

## Task 11: 登录注册页面

**Files:**
- Create: `web/frontend/src/views/Login.vue`
- Create: `web/frontend/src/views/Register.vue`

- [ ] **Step 1: 创建Login.vue**

```vue
<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">GetPayurl Web</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="handleLogin"
            :loading="loading"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
        <div class="register-link">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  loading.value = true
  try {
    await authStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fa;
}

.login-card {
  width: 400px;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

.register-link {
  text-align: center;
  color: #909399;
}

.register-link a {
  color: #409eff;
  text-decoration: none;
}
</style>
```

- [ ] **Step 2: 创建Register.vue**

```vue
<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="register-title">注册账号</h2>
      <el-form :model="form" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名（3-50字符）"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（6-100字符）"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="handleRegister"
            :loading="loading"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>
        <div class="login-link">
          已有账号？
          <router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.warning('两次密码不一致')
    return
  }
  
  loading.value = true
  try {
    await register(form.value.username, form.value.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fa;
}

.register-card {
  width: 400px;
}

.register-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

.login-link {
  text-align: center;
  color: #909399;
}

.login-link a {
  color: #409eff;
  text-decoration: none;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/views/Login.vue web/frontend/src/views/Register.vue
git commit -m "feat: 创建登录注册页面"
```

---

## Task 12: 控制台页面

**Files:**
- Create: `web/frontend/src/views/Dashboard.vue`

- [ ] **Step 1: 创建Dashboard.vue**

```vue
<template>
  <div class="dashboard">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>GetPayurl Web</h1>
          <div class="header-right">
            <span>欢迎，{{ authStore.username }}</span>
            <el-button type="danger" size="small" @click="handleLogout">
              退出登录
            </el-button>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card @click="$router.push('/platform')" class="action-card">
              <el-icon :size="50" color="#409eff"><Setting /></el-icon>
              <h3>平台管理</h3>
              <p>配置店铺账号和商品链接</p>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card @click="$router.push('/order')" class="action-card">
              <el-icon :size="50" color="#67c23a"><Money /></el-icon>
              <h3>订单处理</h3>
              <p>生成支付二维码</p>
            </el-card>
          </el-col>
        </el-row>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>最近订单</span>
            </div>
          </template>
          <el-empty description="暂无订单记录" />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.action-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.action-card h3 {
  margin: 15px 0 10px;
  color: #303133;
}

.action-card p {
  margin: 0;
  color: #909399;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add web/frontend/src/views/Dashboard.vue
git commit -m "feat: 创建控制台页面"
```

---

## Task 13: 平台管理页面

**Files:**
- Create: `web/frontend/src/views/PlatformManage.vue`
- Create: `web/frontend/src/components/PlatformSelector.vue`

- [ ] **Step 1: 创建PlatformSelector.vue**

```vue
<template>
  <el-select v-model="selectedPlatform" placeholder="选择平台" @change="handleChange">
    <el-option
      v-for="platform in platforms"
      :key="platform.code"
      :label="platform.name"
      :value="platform.code"
    />
  </el-select>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { usePlatformStore } from '../stores/platform'

const platformStore = usePlatformStore()
const platforms = ref([])
const selectedPlatform = ref('')

const emit = defineEmits(['change'])

onMounted(async () => {
  await platformStore.loadPlatforms()
  platforms.value = platformStore.platforms
  if (platforms.value.length > 0) {
    selectedPlatform.value = platforms.value[0].code
    handleChange(selectedPlatform.value)
  }
})

const handleChange = (value) => {
  emit('change', value)
}

watch(() => platformStore.platforms, (newVal) => {
  platforms.value = newVal
})
</script>
```

- [ ] **Step 2: 创建PlatformManage.vue**

```vue
<template>
  <div class="platform-manage">
    <el-container>
      <el-header>
        <el-button @click="$router.push('/')">返回首页</el-button>
        <span class="title">平台管理</span>
      </el-header>
      
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>选择平台</span>
              <PlatformSelector @change="handlePlatformChange" />
            </div>
          </template>
          
          <el-form :model="form" label-width="100px">
            <el-form-item label="店铺账号">
              <el-input v-model="form.shop_username" placeholder="请输入店铺账号" />
            </el-form-item>
            
            <el-form-item label="店铺密码">
              <el-input
                v-model="form.shop_password"
                type="password"
                placeholder="请输入店铺密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                @click="handleShopLogin"
                :loading="loginLoading"
              >
                登录店铺
              </el-button>
              <el-tag
                v-if="platformStore.loginStatus.loggedIn"
                type="success"
                style="margin-left: 10px"
              >
                已登录: {{ platformStore.loginStatus.shopName }}
              </el-tag>
            </el-form-item>
            
            <el-divider>商品链接</el-divider>
            
            <el-form-item label="商品链接">
              <div v-for="(url, index) in form.product_urls" :key="index" class="url-item">
                <el-input v-model="form.product_urls[index]" placeholder="输入商品链接" />
                <el-button
                  type="danger"
                  :icon="Delete"
                  @click="removeUrl(index)"
                  style="margin-left: 10px"
                />
              </div>
              <el-button @click="addUrl" style="margin-top: 10px">
                添加链接
              </el-button>
            </el-form-item>
            
            <el-form-item>
              <el-button type="success" @click="saveConfig" :loading="saveLoading">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { usePlatformStore } from '../stores/platform'
import PlatformSelector from '../components/PlatformSelector.vue'

const platformStore = usePlatformStore()
const currentPlatform = ref('')
const loginLoading = ref(false)
const saveLoading = ref(false)

const form = ref({
  shop_username: '',
  shop_password: '',
  product_urls: []
})

onMounted(async () => {
  await platformStore.loadPlatforms()
})

const handlePlatformChange = async (platformCode) => {
  currentPlatform.value = platformCode
  await platformStore.loadConfig(platformCode)
  
  form.value.shop_username = platformStore.config.shop_username || ''
  form.value.shop_password = ''
  form.value.product_urls = [...platformStore.config.product_urls]
}

const handleShopLogin = async () => {
  if (!form.value.shop_username || !form.value.shop_password) {
    ElMessage.warning('请输入账号密码')
    return
  }
  
  loginLoading.value = true
  try {
    const result = await platformStore.shopLogin(
      currentPlatform.value,
      form.value.shop_username,
      form.value.shop_password
    )
    
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('登录失败')
  } finally {
    loginLoading.value = false
  }
}

const addUrl = () => {
  form.value.product_urls.push('')
}

const removeUrl = (index) => {
  form.value.product_urls.splice(index, 1)
}

const saveConfig = async () => {
  saveLoading.value = true
  try {
    await platformStore.updateConfig(currentPlatform.value, {
      shop_username: form.value.shop_username,
      product_urls: form.value.product_urls.filter(url => url.trim())
    })
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saveLoading.value = false
  }
}
</script>

<style scoped>
.platform-manage {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: #fff;
  display: flex;
  align-items: center;
  gap: 20px;
}

.title {
  font-size: 20px;
  font-weight: bold;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.url-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add web/frontend/src/views/PlatformManage.vue web/frontend/src/components/PlatformSelector.vue
git commit -m "feat: 创建平台管理页面"
```

---

## Task 14: 订单处理页面

**Files:**
- Create: `web/frontend/src/views/OrderProcess.vue`
- Create: `web/frontend/src/components/QRCodeDisplay.vue`
- Create: `web/frontend/src/components/LogViewer.vue`

- [ ] **Step 1: 创建LogViewer.vue**

```vue
<template>
  <div class="log-viewer">
    <div class="log-header">处理日志</div>
    <div class="log-content" ref="logContainer">
      <div
        v-for="(log, index) in logs"
        :key="index"
        class="log-item"
        :class="{ 'log-error': log.includes('失败'), 'log-success': log.includes('成功') }"
      >
        {{ log }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

defineProps({
  logs: {
    type: Array,
    default: () => []
  }
})

const logContainer = ref(null)

watch(() => defineProps().logs, async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}, { deep: true })
</script>

<style scoped>
.log-viewer {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
}

.log-header {
  padding: 10px 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: bold;
}

.log-content {
  height: 300px;
  overflow-y: auto;
  padding: 10px;
  font-family: monospace;
  font-size: 12px;
}

.log-item {
  padding: 5px 0;
  color: #606266;
}

.log-success {
  color: #67c23a;
}

.log-error {
  color: #f56c6c;
}
</style>
```

- [ ] **Step 2: 创建QRCodeDisplay.vue**

```vue
<template>
  <div class="qr-display">
    <el-card v-if="qrCode">
      <template #header>
        <div class="card-header">
          <span>支付二维码</span>
          <el-button size="small" @click="copyUrl">复制链接</el-button>
        </div>
      </template>
      <div class="qr-content">
        <img :src="qrCode" alt="支付二维码" class="qr-image" />
        <p class="qr-tip">请使用支付宝扫码支付</p>
      </div>
    </el-card>
    <el-empty v-else description="暂无二维码" />
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'

defineProps({
  qrCode: {
    type: String,
    default: ''
  },
  paymentUrl: {
    type: String,
    default: ''
  }
})

const copyUrl = () => {
  navigator.clipboard.writeText(defineProps().paymentUrl)
  ElMessage.success('链接已复制')
}
</script>

<style scoped>
.qr-display {
  text-align: center;
}

.qr-content {
  padding: 20px;
}

.qr-image {
  max-width: 250px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
}

.qr-tip {
  margin-top: 15px;
  color: #909399;
}
</style>
```

- [ ] **Step 3: 创建OrderProcess.vue**

```vue
<template>
  <div class="order-process">
    <el-container>
      <el-header>
        <el-button @click="$router.push('/')">返回首页</el-button>
        <span class="title">订单处理</span>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>订单配置</template>
              
              <el-form :model="form" label-width="100px">
                <el-form-item label="选择平台">
                  <PlatformSelector @change="handlePlatformChange" />
                </el-form-item>
                
                <el-form-item label="商品链接">
                  <el-select
                    v-model="form.product_url"
                    placeholder="选择或输入商品链接"
                    filterable
                    allow-create
                  >
                    <el-option
                      v-for="url in productUrls"
                      :key="url"
                      :label="url"
                      :value="url"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="新价格">
                  <el-input-number
                    v-model="form.new_price"
                    :min="0.01"
                    :precision="2"
                    :step="0.01"
                  />
                </el-form-item>
                
                <el-form-item>
                  <el-row :gutter="10">
                    <el-col :span="12">
                      <el-button
                        type="primary"
                        @click="handleGetPrice"
                        :loading="priceLoading"
                      >
                        获取价格
                      </el-button>
                    </el-col>
                    <el-col :span="12">
                      <el-button
                        type="success"
                        @click="handleProcessOrder"
                        :loading="orderStore.processing"
                      >
                        生成二维码
                      </el-button>
                    </el-col>
                  </el-row>
                </el-form-item>
              </el-form>
              
              <el-card v-if="orderStore.priceInfo" style="margin-top: 20px">
                <template #header>商品信息</template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="商品名称">
                    {{ orderStore.priceInfo.product_name }}
                  </el-descriptions-item>
                  <el-descriptions-item label="原始价格">
                    ¥{{ orderStore.priceInfo.original_price }}
                  </el-descriptions-item>
                  <el-descriptions-item label="库存">
                    {{ orderStore.priceInfo.stock }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <QRCodeDisplay
              :qr-code="orderStore.qrCode"
              :payment-url="orderStore.paymentUrl"
            />
            <LogViewer :logs="orderStore.logs" style="margin-top: 20px" />
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useOrderStore } from '../stores/order'
import { usePlatformStore } from '../stores/platform'
import PlatformSelector from '../components/PlatformSelector.vue'
import QRCodeDisplay from '../components/QRCodeDisplay.vue'
import LogViewer from '../components/LogViewer.vue'

const orderStore = useOrderStore()
const platformStore = usePlatformStore()
const currentPlatform = ref('')
const priceLoading = ref(false)

const form = ref({
  product_url: '',
  new_price: 0.01
})

const productUrls = computed(() => {
  return platformStore.config.product_urls || []
})

onMounted(async () => {
  await platformStore.loadPlatforms()
})

const handlePlatformChange = async (platformCode) => {
  currentPlatform.value = platformCode
  await platformStore.loadConfig(platformCode)
}

const handleGetPrice = async () => {
  if (!form.value.product_url) {
    ElMessage.warning('请输入商品链接')
    return
  }
  
  priceLoading.value = true
  try {
    const result = await orderStore.getPrice(currentPlatform.value, form.value.product_url)
    if (result.success) {
      ElMessage.success('价格获取成功')
    } else {
      ElMessage.error(result.message || '价格获取失败')
    }
  } catch (error) {
    ElMessage.error('价格获取失败')
  } finally {
    priceLoading.value = false
  }
}

const handleProcessOrder = async () => {
  if (!form.value.product_url) {
    ElMessage.warning('请输入商品链接')
    return
  }
  
  try {
    const result = await orderStore.processOrder(
      currentPlatform.value,
      form.value.product_url,
      form.value.new_price
    )
    
    if (result.success) {
      ElMessage.success('订单处理成功')
    } else {
      ElMessage.error(result.error_message || '订单处理失败')
    }
  } catch (error) {
    ElMessage.error('订单处理失败')
  }
}
</script>

<style scoped>
.order-process {
  min-height: 100vh;
  background: #f5f7fa;
}

.el-header {
  background: #fff;
  display: flex;
  align-items: center;
  gap: 20px;
}

.title {
  font-size: 20px;
  font-weight: bold;
}
</style>
```

- [ ] **Step 4: Commit**

```bash
git add web/frontend/src/views/OrderProcess.vue web/frontend/src/components/
git commit -m "feat: 创建订单处理页面和组件"
```

---

## Task 15: 启动脚本和文档

**Files:**
- Create: `web/start.bat`
- Create: `web/README.md`

- [ ] **Step 1: 创建start.bat**

```batch
@echo off
echo Starting GetPayurl Web Application...
echo.

:: Start backend
echo Starting backend server...
start "Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
echo Starting frontend dev server...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause >nul

:: Kill both processes
taskkill /FI "WINDOWTITLE eq Backend*" /T /F
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F

echo Servers stopped.
```

- [ ] **Step 2: 创建web/README.md**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add web/start.bat web/README.md
git commit -m "feat: 创建启动脚本和文档"
```

---

## 自我审查

**1. 规范覆盖检查**

对照设计文档逐项检查：
- ✅ 技术栈：FastAPI + Vue.js 3 + SQLite + JWT
- ✅ 数据库：3张表（users, platform_configs, order_logs）
- ✅ API设计：认证、平台、订单、配置四大模块
- ✅ 业务逻辑：猴发卡6步流程、四云发卡8步流程（含2.5和3.5）
- ✅ 前端页面：登录、注册、控制台、平台管理、订单处理
- ✅ 状态管理：auth、platform、order三个store
- ✅ 多用户认证：JWT + bcrypt
- ✅ 组件：PlatformSelector、QRCodeDisplay、LogViewer

**2. 占位符扫描**
- 无TBD/TODO
- 所有步骤包含完整代码
- 无"类似Task N"引用

**3. 类型一致性**
- 所有API路径使用 `/api/platforms/{platform_code}` 格式
- 响应模型统一使用Pydantic schemas
- 前端API调用与后端路由一致

**4. 范围检查**
- 聚焦于两个平台的Web化
- 无额外功能（无WebSocket、无Redis、无Docker）

---

**计划完成！**

**执行选项：**

**1. 子代理驱动（推荐）** - 每个Task独立子代理，任务间审查，快速迭代

**2. 内联执行** - 在当前会话使用executing-plans批量执行，检查点审查

您希望使用哪种方式执行？
