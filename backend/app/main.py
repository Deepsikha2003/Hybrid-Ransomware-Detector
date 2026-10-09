import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, SessionLocal, engine
from .ml.pipeline import store
from .models import ModelMetadata, User
from .routers import admin, analysis, auth, insights, reports
from .security import hash_password

logging.basicConfig(level=logging.INFO)


def sync_model_metadata(db: Session) -> None:
    for name, b in store.bundles.items():
        row = db.query(ModelMetadata).filter_by(name=name).first() or ModelMetadata(name=name)
        row.trained_at, row.synthetic, row.metrics, row.features = b.get("trained_at"), bool(b.get("synthetic")), b["metrics"], b["features"]
        db.add(row)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.env == "production" and settings.jwt_secret.startswith("dev-only"):
        raise RuntimeError("Set a strong JWT_SECRET in production")
    Base.metadata.create_all(engine)  # for schema evolution use Alembic migrations
    with SessionLocal() as db:
        if not db.query(User).filter(User.email == settings.admin_email.lower()).first():
            db.add(User(email=settings.admin_email.lower(), full_name="Administrator", password_hash=hash_password(settings.admin_password), role="admin"))
            db.commit()
        store.load()
        sync_model_metadata(db)
    yield


app = FastAPI(title="Hybrid Ransomware Detection System", version="1.0.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, analysis.router, insights.router, reports.router, admin.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "models": list(store.bundles)}


# Serve the built React app (frontend/dist) from the same server when it exists.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (DIST / "index.html").exists():
    if (DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api"):
            raise HTTPException(404)
        f = (DIST / path).resolve()
        if path and f.is_file() and f.is_relative_to(DIST.resolve()):
            return FileResponse(f)
        return FileResponse(DIST / "index.html")
