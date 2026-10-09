from sqlalchemy.orm import Session

from ..ml.fusion import DEFAULT_CONFIG, validate_config
from ..models import SystemSetting


def get_fusion_config(db: Session) -> dict:
    row = db.get(SystemSetting, "fusion")
    return validate_config(row.value if row else DEFAULT_CONFIG)


def set_fusion_config(db: Session, cfg: dict) -> dict:
    cfg = validate_config(cfg)
    row = db.get(SystemSetting, "fusion")
    if row:
        row.value = cfg
    else:
        db.add(SystemSetting(key="fusion", value=cfg))
    db.commit()
    return cfg
