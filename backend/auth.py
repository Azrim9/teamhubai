import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from .models import User
from .dependencies import get_db

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Simple dict-based access for brevity in model implementation
    email = user_data.email
    password = user_data.password
    
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": str(new_user.id)})
    return {"user": {"id": str(new_user.id), "email": new_user.email}, "access_token": access_token}

@router.post("/login")
async def login(user_data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = user_data.email
    password = user_data.password
    
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        expires=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
        secure=False, # Set to True in production
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh")
async def refresh(refresh_token: Optional[str] = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
