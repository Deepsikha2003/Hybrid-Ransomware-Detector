from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import audit, require_roles
from ..ml.fusion import validate_config
from ..ml.pipeline import store
from ..models import AuditLog, User
from ..schemas import FusionConfigIn, RoleIn
from ..services.settings_store import get_fusion_config, set_fusion_config
from ..deps import current_user

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles("admin")


@router.get("/fusion-config")
def read_config(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return get_fusion_config(db)  # readable by all roles (UI shows the active thresholds); writable by admins only


@router.put("/fusion-config")
def write_config(body: FusionConfigIn, request: Request, db: Session = Depends(get_db), user: User = Depends(admin_only)):
    try:
        validate_config(body.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    cfg = set_fusion_config(db, body.model_dump())
    audit(db, request, user, "fusion_config_changed", str(cfg))
    return cfg


@router.get("/users")
def users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "is_active": u.is_active, "created_at": u.created_at.isoformat()} for u in db.query(User).order_by(User.id)]


@router.put("/users/{user_id}")
def update_user(user_id: int, body: RoleIn, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    if u.id == admin.id and (body.role != "admin" or not body.is_active):
        raise HTTPException(400, "You cannot demote or disable your own account")
    u.role, u.is_active = body.role, body.is_active
    db.commit()
    audit(db, request, admin, "user_updated", f"user={u.id} role={u.role} active={u.is_active}")
    return {"ok": True}


@router.get("/audit-logs")
def audit_logs(limit: int = Query(100, ge=1, le=500), action: str = "", db: Session = Depends(get_db), _: User = Depends(admin_only)):
    q = db.query(AuditLog, User.email).outerjoin(User, User.id == AuditLog.user_id).order_by(AuditLog.id.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    return [{"id": l.id, "time": l.created_at.isoformat(), "user": email, "action": l.action, "detail": l.detail, "ip": l.ip} for l, email in q.limit(limit)]


@router.post("/reload-models")
def reload_models(request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    store.load()
    from ..main import sync_model_metadata
    sync_model_metadata(db)
    audit(db, request, admin, "models_reloaded", ",".join(store.bundles))
    return {"loaded": list(store.bundles)}
