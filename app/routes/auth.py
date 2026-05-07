from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from app.db import user_db
from app.utils import security
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

class UserSignup(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str

@router.post("/signup")
async def signup(user: UserSignup):
    print(f"[AUTH] Signup attempt for email: {user.email}")
    existing_user = user_db.get_user_by_email(user.email)
    if existing_user:
        print(f"[AUTH] Signup failed: Email {user.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    print(f"[AUTH] Hashing password for {user.email}...")
    hashed_password = security.get_password_hash(user.password)
    user_data = {
        "full_name": user.full_name,
        "email": user.email,
        "password": hashed_password
    }
    
    print(f"[AUTH] Creating user in DB for {user.email}...")
    new_user = user_db.create_user(user_data)
    if not new_user:
        print(f"[AUTH] Signup failed: Database error for {user.email}")
        raise HTTPException(status_code=500, detail="Could not create user")
    
    print(f"[AUTH] Signup successful for {user.email}")
    access_token = security.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name
        }
    }

@router.post("/login")
async def login(user: UserLogin):
    db_user = user_db.get_user_by_email(user.email)
    if not db_user or not security.verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = security.create_access_token(data={"sub": db_user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": db_user["email"],
            "full_name": db_user.get("full_name")
        }
    }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword):
    db_user = user_db.get_user_by_email(data.email)
    if not db_user:
        # We don't want to reveal if a user exists or not for security
        return {"message": "If the email exists, a reset link has been sent"}
    
    reset_token = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(hours=1)
    user_db.set_reset_token(data.email, reset_token, expiry)
    
    # In a real app, send an email here. For now, we mock it.
    print(f"[MOCK EMAIL] Reset token for {data.email}: {reset_token}")
    
    return {
        "message": "If the email exists, a reset link has been sent",
        "mock_token": reset_token # Remove this in production
    }

@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    db_user = user_db.get_user_by_reset_token(data.token)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    print(f"[AUTH] Hashing new password for token {data.token}...")
    hashed_password = security.get_password_hash(data.new_password)
    success = user_db.update_user_password(db_user["email"], hashed_password)
    
    if not success:
        raise HTTPException(status_code=500, detail="Could not update password")
    
    # Clear the reset token
    user_db.set_reset_token(db_user["email"], None, None)
    
    return {"message": "Password updated successfully"}
