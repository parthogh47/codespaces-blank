from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr

from app.core.config import JWT_ALGORITHM, create_access_token, create_refresh_token, get_jwt_secret
from app.core.db import db
from app.dependencies import get_current_user
from app.services.auth_service import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(input: RegisterRequest, response: Response):
    email = input.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(ObjectId())
    await db.users.insert_one({
        "_id": ObjectId(user_id),
        "email": email,
        "password_hash": hash_password(input.password),
        "name": input.name,
        "role": "user",
        "skills": [],
        "proficiency": {},
        "bio": "",
        "profile_picture": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    response.set_cookie(key="access_token", value=create_access_token(user_id, email), httponly=True, secure=True, samesite="none", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=create_refresh_token(user_id), httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    return {"id": user_id, "email": email, "name": input.name, "role": "user", "skills": [], "proficiency": {}, "bio": "", "profile_picture": None}


@router.post("/login")
async def login(input: LoginRequest, response: Response, request: Request):
    email = input.email.lower()
    ip = request.client.host
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier})

    if attempt and attempt.get("locked_until"):
        if datetime.fromisoformat(attempt["locked_until"]) > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(input.password, user["password_hash"]):
        if attempt:
            new_count = attempt.get("count", 0) + 1
            if new_count >= 5:
                await db.login_attempts.update_one({"identifier": identifier}, {"$set": {"count": new_count, "locked_until": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}})
            else:
                await db.login_attempts.update_one({"identifier": identifier}, {"$set": {"count": new_count}})
        else:
            await db.login_attempts.insert_one({"identifier": identifier, "count": 1})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await db.login_attempts.delete_one({"identifier": identifier})
    user_id = str(user["_id"])
    response.set_cookie(key="access_token", value=create_access_token(user_id, email), httponly=True, secure=True, samesite="none", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=create_refresh_token(user_id), httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    return {"id": user_id, "email": user["email"], "name": user["name"], "role": user.get("role", "user"), "skills": user.get("skills", []), "proficiency": user.get("proficiency", {}), "bio": user.get("bio", ""), "profile_picture": user.get("profile_picture")}


@router.post("/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        response.set_cookie(key="access_token", value=create_access_token(str(user["_id"]), user["email"]), httponly=True, secure=True, samesite="none", max_age=86400, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
