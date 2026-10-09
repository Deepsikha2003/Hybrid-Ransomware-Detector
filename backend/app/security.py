from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

ALGO = "HS256"


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def make_token(sub: int, role: str = "", minutes: int | None = None, kind: str = "access") -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes or settings.jwt_minutes)
    return jwt.encode({"sub": str(sub), "role": role, "kind": kind, "exp": exp}, settings.jwt_secret, algorithm=ALGO)


def read_token(token: str, kind: str = "access") -> dict:
    data = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
    if data.get("kind") != kind:
        raise jwt.InvalidTokenError("wrong token kind")
    return data
