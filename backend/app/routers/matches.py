from datetime import datetime, timezone
import uuid
from typing import Set

from bson import ObjectId
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.db import db
from app.dependencies import get_current_user
from app.services.ai_service import generate_matches_with_ai

router = APIRouter(tags=["matches"])


class MatchGenerateRequest(BaseModel):
    force_refresh: bool = False


@router.get("/matches")
async def get_matches(user: dict = Depends(get_current_user)):
    match_doc = await db.matches.find_one({"user_id": user["id"]})
    if match_doc and match_doc.get("matches"):
        return {"matches": match_doc["matches"], "mini_challenges": match_doc.get("mini_challenges", []), "social_hooks": match_doc.get("social_hooks", [])}

    result = await generate_matches_with_ai(user)
    await db.matches.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], "matches": result.get("matches", []), "mini_challenges": result.get("mini_challenges", []), "social_hooks": result.get("social_hooks", []), "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return result


@router.post("/matches/generate")
async def generate_matches(input: MatchGenerateRequest, user: dict = Depends(get_current_user)):
    result = await generate_matches_with_ai(user)
    await db.matches.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], "matches": result.get("matches", []), "mini_challenges": result.get("mini_challenges", []), "social_hooks": result.get("social_hooks", []), "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return result


@router.get("/achievements")
async def get_achievements(user: dict = Depends(get_current_user)):
    achievements_doc = await db.achievements.find_one({"user_id": user["id"]})
    if not achievements_doc:
        default_achievements = [
            {"id": str(uuid.uuid4()), "title": "Profile Complete", "description": "Complete your profile", "earned": len(user.get("skills", [])) > 0, "icon": "trophy"},
            {"id": str(uuid.uuid4()), "title": "First Match", "description": "Get your first skill match", "earned": False, "icon": "star"},
            {"id": str(uuid.uuid4()), "title": "Collaborator", "description": "Start your first collaboration", "earned": False, "icon": "users"},
        ]
        await db.achievements.insert_one({"user_id": user["id"], "achievements": default_achievements})
        return {"achievements": default_achievements}
    return {"achievements": achievements_doc.get("achievements", [])}


@router.get("/matches/real")
async def get_real_user_matches(user: dict = Depends(get_current_user)):
    user_skills: Set[str] = set(user.get("skills", []))
    if not user_skills:
        return {"matches": []}

    other_users = await db.users.find({"_id": {"$ne": ObjectId(user["id"])}, "role": {"$ne": "admin"}, "skills": {"$exists": True, "$ne": []}}, {"password_hash": 0}).to_list(50)

    matches = []
    for other in other_users:
        other_skills = set(other.get("skills", []))
        if not other_skills:
            continue

        overlap = user_skills & other_skills
        complementary = other_skills - user_skills
        if len(overlap) >= 2 or (len(overlap) >= 1 and len(complementary) >= 1):
            compatibility = "High"
        elif len(overlap) >= 1 or len(complementary) >= 1:
            compatibility = "Medium"
        else:
            continue

        matches.append({
            "id": str(other["_id"]),
            "partner_name": other.get("name", "Unknown"),
            "bio": other.get("bio", ""),
            "profile_picture": other.get("profile_picture"),
            "complementary_skills": list(complementary)[:5],
            "shared_skills": list(overlap)[:5],
            "compatibility": compatibility,
            "is_real_user": True,
            "collaboration_idea": f"You both share interest in {', '.join(list(overlap)[:2]) if overlap else 'related skills'}. {other.get('name', 'They')} can help you with {', '.join(list(complementary)[:2]) if complementary else 'their expertise'}.",
            "conversation_starters": [
                f"Hi {other.get('name', '').split()[0]}! I noticed we both have skills in {list(overlap)[0] if overlap else 'similar areas'}. Want to collaborate?",
                f"Hey! I'm looking to learn more about {list(complementary)[0] if complementary else 'your skills'}. Would you be open to chatting?",
            ],
        })

    matches.sort(key=lambda m: 0 if m["compatibility"] == "High" else 1)
    return {"matches": matches[:10]}
