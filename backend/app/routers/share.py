from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.db import db
from app.dependencies import get_current_user

router = APIRouter(tags=["share"])


class ShareMatchRequest(BaseModel):
    match: Dict[str, Any]


@router.post("/share/match")
async def share_match(input: ShareMatchRequest, user: dict = Depends(get_current_user)):
    token = uuid.uuid4().hex[:16]
    await db.shared_matches.insert_one({
        "token": token,
        "user_id": user["id"],
        "user_name": user.get("name", ""),
        "user_skills": user.get("skills", []),
        "match": input.match,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"token": token, "share_url": f"/share/{token}"}


@router.get("/share/{token}")
async def get_shared_match(token: str):
    share = await db.shared_matches.find_one({"token": token}, {"_id": 0})
    if not share:
        raise HTTPException(status_code=404, detail="Shared match not found")
    return share
