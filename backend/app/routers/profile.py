from datetime import datetime, timezone
import logging
import uuid

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from typing import Dict, List, Optional

from app.core.config import APP_NAME
from app.core.db import db
from app.dependencies import get_current_user
from app.services.storage_service import get_object, put_object

logger = logging.getLogger(__name__)
router = APIRouter(tags=["profile"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    skills: Optional[List[str]] = None
    proficiency: Optional[Dict[str, str]] = None
    bio: Optional[str] = None


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return user


@router.put("/profile")
async def update_profile(input: ProfileUpdate, user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if update_data:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update_data})

    updated_user = await db.users.find_one({"_id": ObjectId(user["id"])}, {"_id": 0, "password_hash": 0})
    updated_user["id"] = user["id"]
    return updated_user


@router.post("/profile/upload-picture")
async def upload_picture(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        path = f"{APP_NAME}/profiles/{user['id']}/{uuid.uuid4()}.{ext}"
        data = await file.read()

        result = put_object(path, data, file.content_type or "image/jpeg")
        await db.files.insert_one({
            "id": str(uuid.uuid4()),
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": result["size"],
            "user_id": user["id"],
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"profile_picture": result["path"]}})
        return {"path": result["path"], "url": f"/api/files/{result['path']}"}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{path:path}")
async def download_file(path: str, user: dict = Depends(get_current_user)):
    record = await db.files.find_one({"storage_path": path, "is_deleted": False})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if record.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=record.get("content_type", content_type))
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")
