import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import UserRegister, UserLogin, TokenOut, UserOut
from app.auth.security import hash_password, verify_password, create_access_token
from app.core.logging_config import mask_email
from app.db.deps import get_db
from app.db import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    """
    logger.info("Registration attempt email=%s", mask_email(payload.email))

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        logger.warning("Registration failed: email already registered email=%s", mask_email(payload.email))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User registered successfully user_id=%s email=%s", user.id, mask_email(user.email))
    return user


@router.post("/login", response_model=TokenOut)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT access token.
    """
    logger.info("Login attempt email=%s", mask_email(payload.email))

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("Login failed email=%s", mask_email(payload.email))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    logger.info("Login successful user_id=%s", user.id)
    return TokenOut(access_token=token)