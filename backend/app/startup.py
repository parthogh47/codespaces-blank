import logging
import os
from datetime import datetime, timezone

from bson import ObjectId

from app.core.db import db
from app.services.auth_service import hash_password, verify_password

logger = logging.getLogger(__name__)


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@skillpartner.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})

    if existing is None:
        await db.users.insert_one({
            "_id": ObjectId(),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "skills": [],
            "proficiency": {},
            "bio": "System Administrator",
            "profile_picture": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")

    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"""# Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh

## Profile Endpoints
- GET /api/profile
- PUT /api/profile
- POST /api/profile/upload-picture

## Match Endpoints
- GET /api/matches
- POST /api/matches/generate

## Other Endpoints
- GET /api/achievements
""")


async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.conversations.create_index("participants")
    await db.conversations.create_index("id", unique=True)
    await db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    await db.shared_matches.create_index("token", unique=True)
    logger.info("Indexes created")
