# 🛡️ Hybrid Ransomware Detection System

AI-powered threat intelligence using hybrid machine learning. A **static** XGBoost model (PE/file-structure features) and a **behavioural** XGBoost model (Sysmon-style process/file/registry/network features) are fused into one risk score, classified as **Benign / Suspicious / Ransomware**, and explained with **SHAP**.

```
Upload (CSV/TXT/LOG) → validate → parse → feature alignment
   ├─ Static model  (XGBoost) ─ P_static ─┐
   └─ Behaviour model (XGBoost) ─ P_behav ┴→ Fusion: 0.6·S + 0.4·B  → thresholds → verdict
                                                      └→ SHAP explanation → PostgreSQL → dashboard / PDF / CSV
```

## Important: what this system does and does not do

* **It scores feature data, not raw binaries.** Uploads are CSV/TXT/LOG containing extracted features (PE header columns, or Sysmon-style event lines). A `.exe` is rejected. Files are parsed as text/data and never executed.
* **Models are not included.** Accuracy figures in the spec (99.88 % etc.) come from your research datasets; they are shown on the Performance page labelled *reported*. The live metrics shown next to them are computed from whatever models you actually train/deploy.
* `python -m app.ml.train --demo` (run automatically by `run.bat`) trains on **synthetic** data purely so the app runs end-to-end. The UI flags this loudly. Don't present its verdicts as real detection.
* Column matching is **by name**. A model only scores an upload if ≥30 % of its feature columns are present (`MIN_FEATURE_COVERAGE`); otherwise that model is skipped and fusion uses the other model alone (and says so).

## Quick start (Windows - no Docker, no database to install)

Requires **Python 3.10-3.12** and **Node.js (LTS)**.

1. Unzip the folder.
2. **Double-click `run.bat`.** First run installs packages, trains the demo models and builds the website (5-10 min). Later runs start in seconds.
3. Your browser opens **http://localhost:8000**. Sign in with `admin@example.com` / `ChangeMe!12345`.
4. Click **New Analysis** and upload a file from `sample_data/`.

Data is stored in `backend/rds.db` (SQLite). Delete that file to reset everything. Close the black window to stop the app.

### Manual run (any OS)
```bash
cd backend && python -m venv .venv && .venv\Scripts\activate     # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.ml.train --demo
cd ../frontend && npm install && npm run build && cd ../backend
uvicorn app.main:app --port 8000                                    # http://localhost:8000
```
For frontend development use `npm run dev` in `frontend/` (http://localhost:5173, proxies `/api` to :8000).

### Optional: PostgreSQL + Docker + Nginx (production-style)
Copy `.env.example` to `.env`, fill it in, put models in `backend/models/`, then `docker compose up -d --build` and open http://localhost:8080. To use PostgreSQL without Docker, `pip install psycopg2-binary` and set `DATABASE_URL=postgresql+psycopg2://user:pass@host/db`.

**SHAP:** uses the `shap` package if installed (`pip install shap`); otherwise XGBoost's built-in exact TreeSHAP, which gives the same values.

## Training on your datasets

```bash
python -m app.ml.train --static-csv data/static.csv --behavior-csv data/behavior.csv --label-col Label
```
Pipeline per dataset: drop duplicates/inf/empty columns → numeric coercion → stratified 80/20 split → variance filter + XGBoost-importance feature selection (top 30) → median imputation → standard scaling → XGBoost (`scale_pos_weight` for imbalance). Labels: numeric `>0` or any string not containing benign/legit/normal/clean/good ⇒ ransomware. Output: `models/{static,behavior}_xgb.joblib` (model + imputer + scaler + selected features + hold-out metrics) and `*_metrics.json`. The admin page's **Reload models** picks up new files without a restart.
Security: `.joblib` files are pickles — only load files you produced.

To use the **log parser** with a behavioural model, that model must be trained on the engineered features in `app/ml/features.py::BEHAVIOR_FEATURES` (or adapt `parse_event_log` to emit your dataset's columns).

## Fusion, thresholds, confidence

`Final = w_static·Static + w_behavior·Behavior` (default 0.6/0.4, normalised to sum 1; admin-editable). `< 0.40` Benign · `0.40–0.80` Suspicious · `≥ 0.80` Ransomware (admin-editable). Threat level: Low / Medium / High (upper half of the Suspicious band, orange) / Critical. For multi-row uploads each model's score is the mean row probability (rows flagged and max row score are stored in `details`).
**Confidence** = `max(risk, 1−risk) × (0.7 + 0.3 × agreement)`, agreement = `1 − |static − behavior|`. It is a heuristic certainty of the verdict, not a calibrated probability.

## API (all under `/api`, JWT bearer unless noted)

| Method & path | Purpose | Role |
|---|---|---|
| POST `/auth/signup` · `/auth/login` · `/auth/forgot-password` · `/auth/reset-password` | Auth (public) | — |
| GET `/auth/me` | Current user | any |
| POST `/upload` (multipart `file`) | Validate, parse, store → `analysis_id` | any |
| POST `/predict` `{analysis_id}` | Run both models, fuse, SHAP, persist | any |
| GET `/analysis/{id}` · POST `/analysis/{id}/notes` | Result detail · analyst notes | any · analyst/admin |
| GET `/shap-analysis?analysis_id=` | SHAP data (local + summary per model) | any |
| GET `/dashboard` · `/analytics` · `/threat-feed` | Cards, charts, live feed | any |
| GET `/history?q=&label=&sort=&page=` | Search/filter/paginate | any |
| GET `/reports` · `/reports/{id}/pdf` · `/reports/{id}/csv` | Reports & export | any |
| GET `/model-performance` | Reported + live metrics (public) | — |
| GET/PUT `/admin/fusion-config` | Weights & thresholds (PUT: admin) | any/admin |
| GET `/admin/users` · PUT `/admin/users/{id}` · GET `/admin/audit-logs` · POST `/admin/reload-models` | Administration | admin |

Roles: **Admin** (everything), **Security Analyst** (sees all analyses, edits notes), **User** (own analyses only). Self-signup always creates `user`; promote via Admin → Users.

## Folder structure
```
backend/app/{main,config,database,models,schemas,security,deps}.py
backend/app/routers/{auth,analysis,insights,reports,admin}.py
backend/app/ml/{features,fusion,pipeline,explain,train,synthetic}.py
backend/app/services/{reports,serializers,settings_store}.py
backend/{schema.sql,tests/,models/}   frontend/src/{pages,components}   sample_data/  scripts/
docker-compose.yml  .env.example
```

## Deployment guide
1. Provision a host with Docker; set DNS. 2. Fill `.env` with strong unique values (the backend refuses to start in `ENV=production` with the dev JWT secret). 3. Terminate TLS in front of the `frontend` container (Caddy / Traefik / certbot + Nginx) and set `CORS_ORIGINS` to your https origin. 4. Put models in `backend/models/`. 5. `docker compose up -d --build`. 6. Back up the `pgdata` and `uploads` volumes.

**Before real production use** (not implemented here): rate limiting / lockout on `/auth/*` and `/upload` (e.g. at the reverse proxy), SMTP for password reset, Alembic migrations, scanning/retention policy for stored uploads, running SHAP in a background worker for very large uploads, and a security review. Short-lived (60 min) JWTs are kept in `localStorage`; if you need stronger XSS resistance, move to httpOnly cookies.
