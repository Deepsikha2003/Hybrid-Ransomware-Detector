import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import audit, current_user
from ..models import User
from ..schemas import ForgotIn, LoginIn, ResetIn, SignupIn
from ..security import hash_password, make_token, read_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("rds.auth")
_DUMMY = hash_password("dummy-password-for-timing")


def _user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role}


@router.post("/signup", status_code=201)
def signup(body: SignupIn, request: Request, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already registered")
    u = User(email=email, full_name=body.full_name.strip(), password_hash=hash_password(body.password), role="user")
    db.add(u); db.commit()
    audit(db, request, u, "signup", email)
    return {"access_token": make_token(u.id, u.role), "user": _user_out(u)}


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email.lower()).first()
    ok = verify_password(body.password, u.password_hash if u else _DUMMY)
    if not (u and ok and u.is_active):
        audit(db, request, None, "login_failed", body.email)
        raise HTTPException(401, "Invalid credentials")
    audit(db, request, u, "login")
    return {"access_token": make_token(u.id, u.role), "user": _user_out(u)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _user_out(user)


@router.post("/forgot-password")
def forgot(body: ForgotIn, request: Request, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email.lower()).first()
    out = {"message": "If that email exists, a reset link has been sent."}
    if u and u.is_active:
        token = make_token(u.id, kind="reset", minutes=30)
        audit(db, request, u, "password_reset_requested")
        # TODO(production): send `token` by email (SMTP/SES). Never return or log it in production.
        if settings.env != "production":
            log.warning("DEV reset token for %s: %s", u.email, token)
            out["dev_token"] = token
    return out


@router.post("/reset-password")
def reset(body: ResetIn, request: Request, db: Session = Depends(get_db)):
    try:
        data = read_token(body.token, kind="reset")
    except jwt.PyJWTError:
        raise HTTPException(400, "Invalid or expired reset token")
    u = db.get(User, int(data["sub"]))
    if not u:
        raise HTTPException(400, "Invalid or expired reset token")
    u.password_hash = hash_password(body.new_password)
    db.commit()
    audit(db, request, u, "password_reset")
    return {"message": "Password updated"}
