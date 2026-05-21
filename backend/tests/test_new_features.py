"""Tests for new features (iteration 3): Real user matching, Conversations/Messaging, Share match."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"

# Skills for two complementary test users
USER_A_SKILLS = ["Python", "Design", "Marketing"]
USER_A_PROF = {"Python": "advanced", "Design": "intermediate", "Marketing": "beginner"}
USER_B_SKILLS = ["Design", "Photography", "Illustration"]
USER_B_PROF = {"Design": "advanced", "Photography": "intermediate", "Illustration": "beginner"}


@pytest.fixture(scope="module")
def user_a():
    """Create and login a real user A with Python/Design/Marketing skills."""
    s = requests.Session()
    email = f"alice_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Pass123!", "name": "Alice Test"})
    assert r.status_code == 200, r.text
    user_id = r.json()["id"]
    # set skills
    r2 = s.put(f"{API}/profile", json={"skills": USER_A_SKILLS, "proficiency": USER_A_PROF, "bio": "Alice bio"})
    assert r2.status_code == 200
    return {"session": s, "id": user_id, "email": email, "name": "Alice Test"}


@pytest.fixture(scope="module")
def user_b():
    """Create and login a real user B with Design/Photography/Illustration."""
    s = requests.Session()
    email = f"bob_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Pass123!", "name": "Bob Test"})
    assert r.status_code == 200, r.text
    user_id = r.json()["id"]
    r2 = s.put(f"{API}/profile", json={"skills": USER_B_SKILLS, "proficiency": USER_B_PROF, "bio": "Bob bio"})
    assert r2.status_code == 200
    return {"session": s, "id": user_id, "email": email, "name": "Bob Test"}


# --- Real User Matching ---
def test_real_matches_returns_real_user(user_a, user_b):
    """GET /api/matches/real should return user B for user A (shared 'Design')."""
    r = user_a["session"].get(f"{API}/matches/real")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "matches" in data
    assert isinstance(data["matches"], list)
    # Should find user B
    ids = [m["id"] for m in data["matches"]]
    assert user_b["id"] in ids, f"User B not in real matches: {ids}"
    # Verify match structure
    b_match = next(m for m in data["matches"] if m["id"] == user_b["id"])
    assert b_match["partner_name"] == "Bob Test"
    assert "Design" in b_match["shared_skills"]
    assert b_match["is_real_user"] is True
    assert b_match["compatibility"] in ["High", "Medium"]
    assert isinstance(b_match["complementary_skills"], list)
    # B's complementary should include Photography or Illustration
    comp = set(b_match["complementary_skills"])
    assert comp & {"Photography", "Illustration"}, f"Expected complementary skills, got {comp}"


def test_real_matches_excludes_self(user_a):
    r = user_a["session"].get(f"{API}/matches/real")
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()["matches"]]
    assert user_a["id"] not in ids


def test_real_matches_unauthenticated():
    r = requests.get(f"{API}/matches/real")
    assert r.status_code == 401


def test_real_matches_empty_for_no_skills():
    """User with no skills gets empty matches."""
    s = requests.Session()
    email = f"noskill_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Pass123!", "name": "NoSkill"})
    assert r.status_code == 200
    r2 = s.get(f"{API}/matches/real")
    assert r2.status_code == 200
    assert r2.json()["matches"] == []


# --- Conversations / Messaging ---
def test_create_conversation(user_a, user_b):
    r = user_a["session"].post(f"{API}/conversations/{user_b['id']}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data
    assert data["partner"]["id"] == user_b["id"]
    assert data["partner"]["name"] == "Bob Test"
    # Save conv id for later
    pytest.conv_id = data["id"]


def test_create_conversation_idempotent(user_a, user_b):
    """Creating again returns same conversation."""
    r = user_a["session"].post(f"{API}/conversations/{user_b['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == pytest.conv_id


def test_create_conversation_self_blocked(user_a):
    r = user_a["session"].post(f"{API}/conversations/{user_a['id']}")
    assert r.status_code == 400


def test_create_conversation_invalid_partner(user_a):
    r = user_a["session"].post(f"{API}/conversations/notarealid")
    assert r.status_code == 400


def test_create_conversation_unauthenticated(user_b):
    r = requests.post(f"{API}/conversations/{user_b['id']}")
    assert r.status_code == 401


def test_list_conversations(user_a, user_b):
    r = user_a["session"].get(f"{API}/conversations")
    assert r.status_code == 200
    convs = r.json()["conversations"]
    assert isinstance(convs, list)
    assert any(c["id"] == pytest.conv_id and c["partner"]["id"] == user_b["id"] for c in convs)


def test_send_message(user_a):
    msg = "Hello Bob, want to collaborate?"
    r = user_a["session"].post(f"{API}/conversations/{pytest.conv_id}/messages", json={"content": msg})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["content"] == msg
    assert data["sender_id"] == user_a["id"]
    assert data["conversation_id"] == pytest.conv_id
    assert "id" in data


def test_send_empty_message_rejected(user_a):
    r = user_a["session"].post(f"{API}/conversations/{pytest.conv_id}/messages", json={"content": "   "})
    assert r.status_code == 400


def test_get_messages(user_a):
    r = user_a["session"].get(f"{API}/conversations/{pytest.conv_id}/messages")
    assert r.status_code == 200
    msgs = r.json()["messages"]
    assert isinstance(msgs, list)
    assert len(msgs) >= 1
    assert msgs[0]["content"] == "Hello Bob, want to collaborate?"
    # Should not have _id (mongo)
    assert "_id" not in msgs[0]


def test_b_can_see_and_reply(user_b):
    """User B should be able to access conversation and reply."""
    # List convs
    r = user_b["session"].get(f"{API}/conversations")
    assert r.status_code == 200
    convs = r.json()["conversations"]
    assert any(c["id"] == pytest.conv_id for c in convs)
    # Get messages
    r2 = user_b["session"].get(f"{API}/conversations/{pytest.conv_id}/messages")
    assert r2.status_code == 200
    # Reply
    r3 = user_b["session"].post(f"{API}/conversations/{pytest.conv_id}/messages", json={"content": "Sure, let's chat!"})
    assert r3.status_code == 200


def test_non_participant_cannot_access():
    """Random user cannot access conversation."""
    s = requests.Session()
    email = f"intruder_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={"email": email, "password": "Pass123!", "name": "Intruder"})
    assert r.status_code == 200
    r2 = s.get(f"{API}/conversations/{pytest.conv_id}/messages")
    assert r2.status_code == 403
    r3 = s.post(f"{API}/conversations/{pytest.conv_id}/messages", json={"content": "spy"})
    assert r3.status_code == 403


def test_get_nonexistent_conversation(user_a):
    r = user_a["session"].get(f"{API}/conversations/nonexistent-id/messages")
    assert r.status_code == 404


# --- Share Match ---
def test_share_match_creates_token(user_a):
    match = {
        "partner_name": "Bob Test",
        "complementary_skills": ["Photography"],
        "shared_skills": ["Design"],
        "compatibility": "High",
        "collaboration_idea": "Test idea",
        "conversation_starters": ["Hi"]
    }
    r = user_a["session"].post(f"{API}/share/match", json={"match": match})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "token" in data
    assert "share_url" in data
    assert len(data["token"]) > 0
    pytest.share_token = data["token"]


def test_get_shared_match_public():
    """Public endpoint, no auth needed."""
    r = requests.get(f"{API}/share/{pytest.share_token}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["token"] == pytest.share_token
    assert data["match"]["partner_name"] == "Bob Test"
    assert data["user_name"] == "Alice Test"
    assert "Design" in data["user_skills"]
    # Mongo _id should be excluded
    assert "_id" not in data


def test_get_shared_match_not_found():
    r = requests.get(f"{API}/share/doesnotexist")
    assert r.status_code == 404


def test_share_match_unauthenticated():
    r = requests.post(f"{API}/share/match", json={"match": {}})
    assert r.status_code == 401
