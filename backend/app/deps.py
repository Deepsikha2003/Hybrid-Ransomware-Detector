import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditLog, User
from .security import read_token

bearer = HTTPBearer(auto_error=False)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        data = read_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(data["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "Account disabled")
    return user


def require_roles(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


def audit(db: Session, request: Request | None, user: User | None, action: str, detail: str = "") -> None:
    ip = request.client.host if request and request.client else ""
    db.add(AuditLog(user_id=user.id if user else None, action=action, detail=detail[:2000], ip=ip))
    db.commit()
