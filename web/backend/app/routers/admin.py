from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User
from app.dependencies import get_current_user
from app.auth import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["管理员"])


# Schema 定义
class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[int] = None
    is_disabled: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: int
    is_disabled: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    success: bool
    users: list[UserResponse]


class MessageResponse(BaseModel):
    success: bool
    message: str


def require_admin(current_user: User = Depends(get_current_user)):
    """验证当前用户是否为管理员"""
    if current_user.username != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取所有用户列表（仅管理员）"""
    users = db.query(User).order_by(User.id).all()
    
    user_list = []
    for user in users:
        user_list.append(UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            is_disabled=user.is_disabled,
            created_at=str(user.created_at) if user.created_at else "",
            updated_at=str(user.updated_at) if user.updated_at else ""
        ))
    
    return UserListResponse(success=True, users=user_list)


@router.put("/users/{user_id}", response_model=MessageResponse)
def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新用户信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能修改admin用户
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能修改管理员账户")
    
    # 更新字段
    if update_data.username is not None:
        # 检查用户名是否已存在
        existing = db.query(User).filter(
            User.username == update_data.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = update_data.username
    
    if update_data.password is not None:
        if len(update_data.password) < 6:
            raise HTTPException(status_code=400, detail="密码长度不能少于6位")
        user.password_hash = get_password_hash(update_data.password)
    
    if update_data.is_admin is not None:
        user.is_admin = update_data.is_admin
    
    if update_data.is_disabled is not None:
        user.is_disabled = update_data.is_disabled
    
    db.commit()
    
    return MessageResponse(success=True, message="用户更新成功")


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除admin用户
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账户")
    
    # 删除用户相关的平台配置
    from app.models import PlatformConfig, OrderLog
    db.query(PlatformConfig).filter(PlatformConfig.user_id == user_id).delete()
    db.query(OrderLog).filter(OrderLog.user_id == user_id).delete()
    
    # 删除用户
    db.delete(user)
    db.commit()
    
    return MessageResponse(success=True, message="用户删除成功")


@router.post("/users/{user_id}/toggle-disable", response_model=MessageResponse)
def toggle_user_disable(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """禁用/启用用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能禁用admin用户
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能禁用管理员账户")
    
    # 切换禁用状态
    user.is_disabled = 1 if user.is_disabled == 0 else 0
    db.commit()
    
    status_text = "已禁用" if user.is_disabled == 1 else "已启用"
    return MessageResponse(success=True, message=f"用户{status_text}")
