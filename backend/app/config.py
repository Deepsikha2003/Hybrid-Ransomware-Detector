import os
from pathlib import Path


def _e(key: str, default: str) -> str:
    return os.environ.get(key, default)


class Settings:
    env = _e("ENV", "development")
    database_url = _e("DATABASE_URL", "sqlite:///./rds.db")  # set to a postgresql+psycopg2:// URL to use PostgreSQL
    jwt_secret = _e("JWT_SECRET", "dev-only-change-me")
    jwt_minutes = int(_e("JWT_EXPIRE_MINUTES", "60"))
    model_dir = Path(_e("MODEL_DIR", "./models"))
    upload_dir = Path(_e("UPLOAD_DIR", "./uploads"))
    max_upload_mb = int(_e("MAX_UPLOAD_MB", "20"))
    max_rows = int(_e("MAX_ROWS", "50000"))
    min_feature_coverage = float(_e("MIN_FEATURE_COVERAGE", "0.3"))
    admin_email = _e("ADMIN_EMAIL", "admin@example.com")
    admin_password = _e("ADMIN_PASSWORD", "ChangeMe!12345")
    cors_origins = [o for o in _e("CORS_ORIGINS", "http://localhost:5173").split(",") if o]


settings = Settings()
