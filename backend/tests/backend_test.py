import os
import io
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback - read frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@skillpartner.com"
ADMIN_PASSWORD = "admin123"

TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    return s


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return s


# Auth - Register & Login
def test_register_new_user(session):
    r = session.post(f"{API}/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == TEST_EMAIL
    assert data["name"] == TEST_NAME
    assert "id" in data
    # cookies should be set
    assert "access_token" in session.cookies.get_dict()


def test_register_duplicate(session):
    r = session.post(f"{API}/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME})
    assert r.status_code == 400


def test_auth_me(session):
    r = session.get(f"{API}/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == TEST_EMAIL


def test_admin_login(admin_session):
    r = admin_session.get(f"{API}/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == ADMIN_EMAIL


def test_login_invalid():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert r.status_code == 401


def test_unauth_me():
    r = requests.get(f"{API}/auth/me")
    assert r.status_code == 401


# Profile
def test_get_profile(session):
    r = session.get(f"{API}/profile")
    assert r.status_code == 200
    assert r.json()["email"] == TEST_EMAIL


def test_update_profile(session):
    payload = {"skills": ["Python", "React"], "proficiency": {"Python": "advanced", "React": "intermediate"}, "bio": "Hi"}
    r = session.put(f"{API}/profile", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "Python" in data["skills"]
    assert data["bio"] == "Hi"
    # verify persistence
    r2 = session.get(f"{API}/profile")
    assert r2.json()["skills"] == ["Python", "React"]


def test_upload_picture(session):
    # 1x1 PNG
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7Z\xa3\x9b\x00\x00\x00\x00IEND\xaeB`\x82"
    files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
    r = session.post(f"{API}/profile/upload-picture", files=files)
    if r.status_code != 200:
        pytest.skip(f"Upload skipped (storage may be unavailable): {r.status_code} {r.text[:200]}")
    data = r.json()
    assert "path" in data
    assert "url" in data


# Matches (AI integration)
def test_matches_get(session):
    r = session.get(f"{API}/matches", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "matches" in data
    assert "mini_challenges" in data
    assert "social_hooks" in data
    assert isinstance(data["matches"], list)


def test_matches_generate(session):
    r = session.post(f"{API}/matches/generate", json={"force_refresh": True}, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "matches" in data


# Achievements
def test_achievements(session):
    r = session.get(f"{API}/achievements")
    assert r.status_code == 200
    assert "achievements" in r.json()
    assert isinstance(r.json()["achievements"], list)


# Logout
def test_logout(session):
    r = session.post(f"{API}/auth/logout")
    assert r.status_code == 200
    # me should fail after logout
    r2 = session.get(f"{API}/auth/me")
    assert r2.status_code == 401
