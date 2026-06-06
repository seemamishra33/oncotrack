"""
auth.py
=======

Checks username and password against the database.
"""

import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.Connection import get_db
from database.Models import User

logger = logging.getLogger("oncotrack.auth")


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Simple password check — compares plain text.
    Good enough for a portfolio demo.
    """
    return plain_password == stored_password


def authenticate_user(
    username : str,
    password : str,
    db       : Session
) -> User:
    """
    Check username and password against the database.
    Returns the user if valid, raises 401 if not.
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        logger.warning(f"Login failed - user not found: {username}")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Incorrect username or password"
        )

    if not verify_password(password, user.password_hash):
        logger.warning(f"Login failed - wrong password: {username}")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail      = "Inactive user account"
        )

    logger.info(f"Login successful: {username} ({user.role})")
    return user


def get_current_user(
    username : str,
    db       : Session = Depends(get_db)
) -> User:
    """Fetch and return a user by username."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "User not found"
        )
    return user