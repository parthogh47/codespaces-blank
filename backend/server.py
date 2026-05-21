from dotenv import load_dotenv
from pathlib import Path
import logging
import os

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.core.db import client
from app.routers.auth import router as auth_router
from app.routers.matches import router as matches_router
from app.routers.messages import router as messages_router
from app.routers.profile import router as profile_router
from app.routers.share import router as share_router
from app.services.storage_service import init_storage
from app.startup import ensure_indexes, seed_admin

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(matches_router)
api_router.include_router(messages_router)
api_router.include_router(share_router)


@app.on_event("startup")
async def startup():
    try:
        await ensure_indexes()
        init_storage()
        await seed_admin()
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


app.include_router(api_router)

# Optional static frontend hosting (for environments without Node runtime).
FRONTEND_BUILD_DIR = os.environ.get("FRONTEND_BUILD_DIR", str(ROOT_DIR.parent / "frontend" / "build"))
if Path(FRONTEND_BUILD_DIR).exists():
    assets_dir = Path(FRONTEND_BUILD_DIR) / "static"
    if assets_dir.exists():
        app.mount("/static", StaticFiles(directory=str(assets_dir)), name="static")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api"):
            return {"detail": "Not Found"}
        index_file = Path(FRONTEND_BUILD_DIR) / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"detail": "Frontend build not found"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
