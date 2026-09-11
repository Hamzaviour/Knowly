from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.auth import hash_password, create_access_token, verify_password, require_user
from app.config import settings
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be at most 100 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address")
        return v


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str]
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address")
        return v


class LoginResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str]
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    """Empty body — client revokes its stored token."""
    pass


class UserInfo(BaseModel):
    id: str
    email: str
    name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed = hash_password(body.password)
    user = User(
        email=body.email.lower().strip(),
        name=body.name.strip(),
        hashed_password=hashed,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        name=user.name,
        access_token=token,
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(user.id)
    return LoginResponse(
        user_id=user.id,
        email=user.email,
        name=user.name,
        access_token=token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    """Client-side token revocation. No server state to clear for JWT."""
    return None


@router.get("/me", response_model=UserInfo)
def me(user: User = require_user()):
    return UserInfo(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
