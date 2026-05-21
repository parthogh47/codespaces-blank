from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.db import db
from app.dependencies import get_current_user

router = APIRouter(tags=["messages"])


class SendMessageRequest(BaseModel):
    content: str = Field(..., max_length=5000)


@router.post("/conversations/{partner_id}")
async def create_or_get_conversation(partner_id: str, user: dict = Depends(get_current_user)):
    try:
        partner = await db.users.find_one({"_id": ObjectId(partner_id)}, {"password_hash": 0})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid partner ID")

    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    if partner_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    participants = sorted([user["id"], partner_id])
    existing = await db.conversations.find_one({"participants": participants})
    if existing:
        return {"id": existing["id"], "participants": existing["participants"], "partner": {"id": partner_id, "name": partner.get("name", ""), "profile_picture": partner.get("profile_picture")}, "created_at": existing.get("created_at")}

    conv_id = str(uuid.uuid4())
    conv_doc: Dict[str, Any] = {
        "id": conv_id,
        "participants": participants,
        "last_message": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.conversations.insert_one(dict(conv_doc))
    return {"id": conv_id, "participants": participants, "partner": {"id": partner_id, "name": partner.get("name", ""), "profile_picture": partner.get("profile_picture")}, "created_at": conv_doc["created_at"]}


@router.get("/conversations")
async def list_conversations(user: dict = Depends(get_current_user)):
    convs = await db.conversations.find({"participants": user["id"]}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    enriched = []
    for c in convs:
        partner_id = next((p for p in c["participants"] if p != user["id"]), None)
        if not partner_id:
            continue
        try:
            partner = await db.users.find_one({"_id": ObjectId(partner_id)}, {"password_hash": 0})
        except Exception:
            partner = None

        enriched.append({
            "id": c["id"],
            "partner": {"id": partner_id, "name": partner.get("name", "Unknown") if partner else "Unknown", "profile_picture": partner.get("profile_picture") if partner else None},
            "last_message": c.get("last_message"),
            "updated_at": c.get("updated_at"),
        })
    return {"conversations": enriched}


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str, user: dict = Depends(get_current_user)):
    conv = await db.conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user["id"] not in conv["participants"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await db.messages.find({"conversation_id": conv_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {"messages": messages}


@router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: str, input: SendMessageRequest, user: dict = Depends(get_current_user)):
    conv = await db.conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user["id"] not in conv["participants"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if not input.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    msg_doc = {
        "id": msg_id,
        "conversation_id": conv_id,
        "sender_id": user["id"],
        "sender_name": user.get("name", ""),
        "content": input.content.strip(),
        "created_at": now,
    }
    await db.messages.insert_one(dict(msg_doc))

    await db.conversations.update_one({"id": conv_id}, {"$set": {"last_message": {"content": input.content.strip()[:100], "sender_id": user["id"], "created_at": now}, "updated_at": now}})

    achievements_doc = await db.achievements.find_one({"user_id": user["id"]})
    if achievements_doc:
        for a in achievements_doc.get("achievements", []):
            if a.get("title") == "Collaborator" and not a.get("earned"):
                a["earned"] = True
        await db.achievements.update_one({"user_id": user["id"]}, {"$set": {"achievements": achievements_doc["achievements"]}})

    return msg_doc
