from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, Header, Query, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import requests
import json
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Constants
JWT_ALGORITHM = "HS256"
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "skillpartner"
storage_key = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Helper Functions - Password
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# Helper Functions - JWT
def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = payload["sub"]
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Helper Functions - Storage
def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    logger.info("Storage initialized")
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key, "Content-Type": content_type}, data=data, timeout=120)
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple[bytes, str]:
    key = init_storage()
    resp = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Helper Functions - AI Matchmaking
async def generate_matches_with_ai(user_profile: dict) -> dict:
    try:
        skills = user_profile.get("skills", [])
        proficiency = user_profile.get("proficiency", {})
        
        skills_text = ", ".join([f"{s} ({proficiency.get(s, 'beginner')})" for s in skills])
        
        prompt = f"""You are an AI system powering a Skill Partner Finder app. A user wants to learn or improve these skills: {skills_text}.

Generate a JSON response with:
1. 3-5 ideal learning partners (fictional profiles with complementary skills)
2. 2-3 mini-challenges related to their skills
3. 2-3 social hooks or achievement ideas

Format:
{{
  "matches": [
    {{
      "partner_name": "Name",
      "complementary_skills": ["skill1", "skill2"],
      "compatibility": "High/Medium/Low",
      "collaboration_idea": "Short actionable plan",
      "conversation_starters": ["Starter1", "Starter2"]
    }}
  ],
  "mini_challenges": ["Challenge 1", "Challenge 2"],
  "social_hooks": ["Achievement to share", "Invite friends prompt"]
}}

Only return valid JSON, nothing else."""
        
        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"match_{user_profile.get('id', 'default')}",
            system_message="You are a helpful AI assistant that generates skill matching data. Respond with raw JSON only, no markdown code fences or additional text."
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Clean markdown code fences from response
        cleaned_response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip(), flags=re.MULTILINE).strip()
        
        # Fallback: extract JSON between first { and last }
        if not cleaned_response.startswith('{'):
            start = cleaned_response.find('{')
            end = cleaned_response.rfind('}')
            if start != -1 and end != -1:
                cleaned_response = cleaned_response[start:end+1]
        
        result = json.loads(cleaned_response)
        
        # Validate result has required fields
        if not result.get("matches") or len(result["matches"]) == 0:
            logger.warning("AI returned empty matches, using fallback")
            raise ValueError("Empty matches from AI")
        
        return result
    except Exception as e:
        logger.error(f"AI matchmaking error: {e}")
        # Return fallback with error flag
        return {
            "matches": [],
            "mini_challenges": [f"Add more skills to get better matches", "Try refreshing your profile"],
            "social_hooks": ["Share your profile", "Invite a friend"],
            "error": True,
            "error_message": "Failed to generate AI matches. Please try again."
        }

# Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    skills: Optional[List[str]] = None
    proficiency: Optional[Dict[str, str]] = None
    bio: Optional[str] = None

class MatchGenerateRequest(BaseModel):
    force_refresh: bool = False

# Auth Endpoints
@api_router.post("/auth/register")
async def register(input: RegisterRequest, response: Response):
    email = input.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    from bson import ObjectId
    user_id = str(ObjectId())
    hashed = hash_password(input.password)
    
    user_doc = {
        "_id": ObjectId(user_id),
        "email": email,
        "password_hash": hashed,
        "name": input.name,
        "role": "user",
        "skills": [],
        "proficiency": {},
        "bio": "",
        "profile_picture": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": email,
        "name": input.name,
        "role": "user",
        "skills": [],
        "proficiency": {},
        "bio": "",
        "profile_picture": None
    }

@api_router.post("/auth/login")
async def login(input: LoginRequest, response: Response, request: Request):
    email = input.email.lower()
    
    # Check brute force
    ip = request.client.host
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    
    if attempt and attempt.get("locked_until"):
        locked_until = datetime.fromisoformat(attempt["locked_until"])
        if locked_until > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(input.password, user["password_hash"]):
        # Increment failed attempts
        if attempt:
            new_count = attempt.get("count", 0) + 1
            if new_count >= 5:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                await db.login_attempts.update_one(
                    {"identifier": identifier},
                    {"$set": {"count": new_count, "locked_until": locked_until.isoformat()}}
                )
            else:
                await db.login_attempts.update_one({"identifier": identifier}, {"$set": {"count": new_count}})
        else:
            await db.login_attempts.insert_one({"identifier": identifier, "count": 1})
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Clear attempts
    await db.login_attempts.delete_one({"identifier": identifier})
    
    from bson import ObjectId
    user_id = str(user["_id"])
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": user["email"],
        "name": user["name"],
        "role": user.get("role", "user"),
        "skills": user.get("skills", []),
        "proficiency": user.get("proficiency", {}),
        "bio": user.get("bio", ""),
        "profile_picture": user.get("profile_picture")
    }

@api_router.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

@api_router.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id = str(user["_id"])
        access_token = create_access_token(user_id, user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
        
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Profile Endpoints
@api_router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return user

@api_router.put("/profile")
async def update_profile(input: ProfileUpdate, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    if update_data:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"_id": ObjectId(user["id"])}, {"_id": 0, "password_hash": 0})
    updated_user["id"] = user["id"]
    return updated_user

@api_router.post("/profile/upload-picture")
async def upload_picture(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        path = f"{APP_NAME}/profiles/{user['id']}/{uuid.uuid4()}.{ext}"
        data = await file.read()
        
        result = put_object(path, data, file.content_type or "image/jpeg")
        
        # Store in DB
        from bson import ObjectId
        file_doc = {
            "id": str(uuid.uuid4()),
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": result["size"],
            "user_id": user["id"],
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.files.insert_one(file_doc)
        
        # Update user profile
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"profile_picture": result["path"]}})
        
        return {"path": result["path"], "url": f"/api/files/{result['path']}"}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/files/{path:path}")
async def download_file(path: str, user: dict = Depends(get_current_user)):
    record = await db.files.find_one({"storage_path": path, "is_deleted": False})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Auth check: users can only access their own files
    if record.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=record.get("content_type", content_type))
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")

# Match Endpoints
@api_router.get("/matches")
async def get_matches(user: dict = Depends(get_current_user)):
    # Check if matches exist in DB
    from bson import ObjectId
    match_doc = await db.matches.find_one({"user_id": user["id"]})
    
    if match_doc and match_doc.get("matches"):
        return {
            "matches": match_doc["matches"],
            "mini_challenges": match_doc.get("mini_challenges", []),
            "social_hooks": match_doc.get("social_hooks", [])
        }
    
    # Generate new matches
    result = await generate_matches_with_ai(user)
    
    # Store in DB
    await db.matches.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], "matches": result.get("matches", []), "mini_challenges": result.get("mini_challenges", []), "social_hooks": result.get("social_hooks", []), "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return result

@api_router.post("/matches/generate")
async def generate_matches(input: MatchGenerateRequest, user: dict = Depends(get_current_user)):
    result = await generate_matches_with_ai(user)
    
    # Store in DB
    await db.matches.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], "matches": result.get("matches", []), "mini_challenges": result.get("mini_challenges", []), "social_hooks": result.get("social_hooks", []), "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return result

# Achievements Endpoint
@api_router.get("/achievements")
async def get_achievements(user: dict = Depends(get_current_user)):
    achievements_doc = await db.achievements.find_one({"user_id": user["id"]})
    
    if not achievements_doc:
        # Create default achievements
        default_achievements = [
            {"id": str(uuid.uuid4()), "title": "Profile Complete", "description": "Complete your profile", "earned": len(user.get("skills", [])) > 0, "icon": "trophy"},
            {"id": str(uuid.uuid4()), "title": "First Match", "description": "Get your first skill match", "earned": False, "icon": "star"},
            {"id": str(uuid.uuid4()), "title": "Collaborator", "description": "Start your first collaboration", "earned": False, "icon": "users"}
        ]
        await db.achievements.insert_one({"user_id": user["id"], "achievements": default_achievements})
        return {"achievements": default_achievements}
    
    return {"achievements": achievements_doc.get("achievements", [])}

# Admin Seeding
async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@skillpartner.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    
    if existing is None:
        from bson import ObjectId
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "_id": ObjectId(),
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "role": "admin",
            "skills": [],
            "proficiency": {},
            "bio": "System Administrator",
            "profile_picture": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")
    
    # Write test credentials
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

@app.on_event("startup")
async def startup():
    try:
        # Create indexes
        await db.users.create_index("email", unique=True)
        await db.login_attempts.create_index("identifier")
        logger.info("Indexes created")
        
        # Initialize storage
        init_storage()
        
        # Seed admin
        await seed_admin()
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)