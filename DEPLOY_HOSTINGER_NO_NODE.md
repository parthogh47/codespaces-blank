# Deploy on Hostinger (No Node.js Runtime)

This project can run on hosts that do **not** support Node runtime by serving a prebuilt React bundle from FastAPI.

## 1) Build frontend locally (on your machine)

```bash
cd frontend
npm install
npm run build
```

This creates `frontend/build/`.

## 2) Upload repo including `frontend/build/`

Upload the full repo to your Hostinger file manager/VPS. Ensure `frontend/build/index.html` exists on server.

## 3) Configure backend env

In `backend/.env` set:

```env
MONGO_URL=...
DB_NAME=...
JWT_SECRET=...
EMERGENT_LLM_KEY=...
CORS_ORIGINS=https://your-domain.com
# Optional override:
# FRONTEND_BUILD_DIR=/absolute/path/to/frontend/build
```

## 4) Run only Python backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

FastAPI now:
- serves API under `/api/*`
- serves React static assets under `/static/*`
- serves SPA routes (`/`, `/dashboard`, `/messages`, etc.) from `frontend/build/index.html`

## 5) Nginx (optional but recommended)

Proxy your domain to `127.0.0.1:8000`.

