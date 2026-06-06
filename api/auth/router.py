"""
router.py
=========
Simple auth endpoints for demo project.

POST /auth/login   -> checks username/password, returns user info
GET  /auth/me      -> returns user info by username
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.Connection import get_db
from database.Models import User
from database.Schemas import UserResponse
from api.auth.auth import authenticate_user

logger = logging.getLogger("oncotrack.auth.router")
router = APIRouter()


# Simple login request schema
class LoginRequest(BaseModel):
    username : str
    password : str


class LoginResponse(BaseModel):
    message  : str
    username : str
    role     : str
    user_id  : int


@router.post("/login", response_model=LoginResponse)
def login(
    data : LoginRequest,
    db   : Session = Depends(get_db)
):
    """
    Login with username and password.
    Returns user info if credentials are correct.
    """
    user = authenticate_user(data.username, data.password, db)
    return LoginResponse(
        message  = f"Welcome {user.username}!",
        username = user.username,
        role     = user.role,
        user_id  = user.id
    )


@router.get("/me/{username}", response_model=UserResponse)
def get_me(
    username : str,
    db       : Session = Depends(get_db)
):
    """Get user info by username."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user