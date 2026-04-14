from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import auth, platforms, orders, config

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(orders.router)
app.include_router(config.router)


@app.on_event("startup")
def on_startup():
    """应用启动时创建表"""
    create_tables()


@app.get("/")
def root():
    return {"message": "GetPayurl Web API", "version": "1.0.0"}
