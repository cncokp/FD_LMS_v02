"""
FD-LMS Role-Based Access Control (RBAC) Authentication Module
Supports session cookies (HttpOnly) and Bearer token headers.
Roles:
  - admin: Division Administrator (all ranges, full admin portal, schema mapping, upload)
  - range_officer: Range Officer (scoped to assigned Range, e.g. National Park Range, Bhawal Range)
  - beat_officer: Beat Officer (scoped to assigned Beat, e.g. Park Beat, Baupara Beat)
  - viewer: Read-only access to interactive map & dashboards
"""

import os
import time
import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "fd-lms-super-secret-rbac-key-2026").strip()
TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days validity

# Standard pre-configured accounts
SEED_USERS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "password": os.getenv("ADMIN_PASSWORD", "admin123").strip(),
        "role": "admin",
        "role_title": "Division Forest Officer (DFO)",
        "full_name": "Division Administrator",
        "division": "Biodiversity Conservation Division",
        "assigned_range": None,
        "assigned_beat": None,
        "can_upload": True,
        "can_edit": True
    },
    "ro_national_park": {
        "username": "ro_national_park",
        "password": "range123",
        "role": "range_officer",
        "role_title": "Range Officer (National Park Range)",
        "full_name": "Range Officer - National Park",
        "division": "Biodiversity Conservation Division",
        "assigned_range": "National Park Range",
        "assigned_beat": None,
        "can_upload": False,
        "can_edit": True
    },
    "ro_bhawal": {
        "username": "ro_bhawal",
        "password": "range123",
        "role": "range_officer",
        "role_title": "Range Officer (Bhawal Range)",
        "full_name": "Range Officer - Bhawal",
        "division": "Biodiversity Conservation Division",
        "assigned_range": "Bhawal Range",
        "assigned_beat": None,
        "can_upload": False,
        "can_edit": True
    },
    "bo_park": {
        "username": "bo_park",
        "password": "beat123",
        "role": "beat_officer",
        "role_title": "Beat Officer (Park Beat)",
        "full_name": "Beat Officer - Park Beat",
        "division": "Biodiversity Conservation Division",
        "assigned_range": "National Park Range",
        "assigned_beat": "Park Beat",
        "can_upload": False,
        "can_edit": False
    },
    "bo_baupara": {
        "username": "bo_baupara",
        "password": "beat123",
        "role": "beat_officer",
        "role_title": "Beat Officer (Baupara Beat)",
        "full_name": "Beat Officer - Baupara Beat",
        "division": "Biodiversity Conservation Division",
        "assigned_range": "National Park Range",
        "assigned_beat": "Baupara Beat",
        "can_upload": False,
        "can_edit": False
    },
    "guest": {
        "username": "guest",
        "password": "guest123",
        "role": "viewer",
        "role_title": "Guest / Public Observer",
        "full_name": "Public Viewer",
        "division": "Biodiversity Conservation Division",
        "assigned_range": None,
        "assigned_beat": None,
        "can_upload": False,
        "can_edit": False
    }
}


try:
    from server import db
except ImportError:
    import db


def hash_password(password: str) -> str:
    """Hash password using salted SHA256"""
    salt = "fd_salt_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(raw_password: str, hashed_str: str) -> bool:
    """Check raw password against hash or plain text fallback"""
    if not raw_password or not hashed_str:
        return False
    # Check salted hash
    expected = hash_password(raw_password)
    if hmac.compare_digest(expected, hashed_str):
        return True
    # Fallback to direct comparison for seed passwords
    return hmac.compare_digest(raw_password, hashed_str)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    if not username or not password:
        return None
    username_clean = username.strip().lower()
    
    # 1. Try PostgreSQL if available
    try:
        if db.is_local_pg_enabled():
            with db.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, username, password_hash, full_name, role, role_title,
                               division, assigned_range, assigned_beat, can_upload, can_edit, is_active
                        FROM users
                        WHERE LOWER(username) = %s AND is_active = TRUE;
                    """, (username_clean,))
                    row = cur.fetchone()
                    if row:
                        if verify_password(password.strip(), row["password_hash"]):
                            u = dict(row)
                            del u["password_hash"]
                            return u
    except Exception as e:
        print(f"[AUTH] PostgreSQL user lookup failed, falling back: {e}")

    # 2. Check seed accounts
    if username_clean in SEED_USERS:
        u = SEED_USERS[username_clean]
        if hmac.compare_digest(password.strip(), u["password"]):
            # Return safe copy without password
            safe_u = dict(u)
            del safe_u["password"]
            return safe_u

    return None


def get_all_users() -> List[Dict[str, Any]]:
    """Return all users without password hashes"""
    users = []
    try:
        if db.is_local_pg_enabled():
            with db.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, username, full_name, role, role_title, division,
                               assigned_range, assigned_beat, can_upload, can_edit, is_active,
                               created_at, updated_at
                        FROM users
                        ORDER BY id ASC;
                    """)
                    rows = cur.fetchall()
                    for r in rows:
                        d = dict(r)
                        if d.get("created_at"):
                            d["created_at"] = str(d["created_at"])
                        if d.get("updated_at"):
                            d["updated_at"] = str(d["updated_at"])
                        users.append(d)
            if users:
                return users
    except Exception as e:
        print(f"[AUTH] get_all_users DB query failed: {e}")

    # Fallback to seed users list
    idx = 1
    for k, v in SEED_USERS.items():
        u = dict(v)
        u["id"] = idx
        idx += 1
        if "password" in u:
            del u["password"]
        u["is_active"] = True
        users.append(u)
    return users


def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user in PostgreSQL"""
    username = str(user_data.get("username", "")).strip().lower()
    raw_password = str(user_data.get("password", "user123")).strip()
    full_name = str(user_data.get("full_name", "")).strip() or username
    role = str(user_data.get("role", "viewer")).strip()
    role_title = str(user_data.get("role_title", "")).strip() or role.replace("_", " ").title()
    division = str(user_data.get("division", "Biodiversity Conservation Division")).strip()
    assigned_range = user_data.get("assigned_range") or None
    assigned_beat = user_data.get("assigned_beat") or None
    can_upload = bool(user_data.get("can_upload", False))
    can_edit = bool(user_data.get("can_edit", False))
    is_active = bool(user_data.get("is_active", True))

    if not username or not raw_password:
        raise ValueError("Username and password are required")

    pw_hash = hash_password(raw_password)

    if db.is_local_pg_enabled():
        with db.get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, full_name, role, role_title,
                                       division, assigned_range, assigned_beat, can_upload, can_edit, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, username, full_name, role, role_title, division,
                              assigned_range, assigned_beat, can_upload, can_edit, is_active, created_at;
                """, (username, pw_hash, full_name, role, role_title, division,
                      assigned_range, assigned_beat, can_upload, can_edit, is_active))
                row = cur.fetchone()
                conn.commit()
                res = dict(row)
                if res.get("created_at"):
                    res["created_at"] = str(res["created_at"])
                return res

    return {"username": username, "full_name": full_name, "role": role}


def update_user(user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user fields, role, or password"""
    if not db.is_local_pg_enabled():
        return None

    with db.get_pg_connection() as conn:
        with conn.cursor() as cur:
            fields = []
            params = []
            
            if "full_name" in user_data:
                fields.append("full_name = %s")
                params.append(user_data["full_name"])
            if "role" in user_data:
                fields.append("role = %s")
                params.append(user_data["role"])
            if "role_title" in user_data:
                fields.append("role_title = %s")
                params.append(user_data["role_title"])
            if "division" in user_data:
                fields.append("division = %s")
                params.append(user_data["division"])
            if "assigned_range" in user_data:
                fields.append("assigned_range = %s")
                params.append(user_data["assigned_range"])
            if "assigned_beat" in user_data:
                fields.append("assigned_beat = %s")
                params.append(user_data["assigned_beat"])
            if "can_upload" in user_data:
                fields.append("can_upload = %s")
                params.append(bool(user_data["can_upload"]))
            if "can_edit" in user_data:
                fields.append("can_edit = %s")
                params.append(bool(user_data["can_edit"]))
            if "is_active" in user_data:
                fields.append("is_active = %s")
                params.append(bool(user_data["is_active"]))
            if user_data.get("password"):
                fields.append("password_hash = %s")
                params.append(hash_password(user_data["password"].strip()))

            fields.append("updated_at = NOW()")
            params.append(user_id)

            sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s RETURNING id, username, full_name, role, role_title, division, assigned_range, assigned_beat, can_upload, can_edit, is_active, updated_at;"
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
            conn.commit()
            if row:
                res = dict(row)
                if res.get("updated_at"):
                    res["updated_at"] = str(res["updated_at"])
                return res
            return None


def delete_user(user_id: int) -> bool:
    """Delete a user from PostgreSQL"""
    if not db.is_local_pg_enabled():
        return False
    with db.get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
            deleted = cur.fetchone()
            conn.commit()
            return bool(deleted)


def create_access_token(user_data: Dict[str, Any]) -> str:
    expires_at = int(time.time()) + TOKEN_EXPIRY_SECONDS
    payload = {
        "username": user_data.get("username"),
        "role": user_data.get("role", "viewer"),
        "role_title": user_data.get("role_title", "User"),
        "full_name": user_data.get("full_name", ""),
        "division": user_data.get("division", "Biodiversity Conservation Division"),
        "assigned_range": user_data.get("assigned_range"),
        "assigned_beat": user_data.get("assigned_beat"),
        "can_upload": user_data.get("can_upload", False),
        "can_edit": user_data.get("can_edit", False),
        "expires_at": expires_at
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")
    
    sig = hmac.new(
        ADMIN_SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{sig}"


def verify_token(token_str: str) -> Optional[Dict[str, Any]]:
    if not token_str:
        return None
    try:
        parts = token_str.split(".")
        if len(parts) != 2:
            # Fallback to legacy single-user token format
            subparts = token_str.split(":")
            if len(subparts) == 3:
                u, exp_str, s = subparts
                if time.time() > int(exp_str):
                    return None
                expected_s = hmac.new(ADMIN_SECRET_KEY.encode("utf-8"), f"{u}:{exp_str}".encode("utf-8"), hashlib.sha256).hexdigest()
                if hmac.compare_digest(s, expected_s):
                    return SEED_USERS.get(u, {
                        "username": u, "role": "admin", "role_title": "Administrator",
                        "assigned_range": None, "assigned_beat": None, "can_upload": True, "can_edit": True
                    })
            return None
            
        payload_b64, sig = parts
        expected_sig = hmac.new(
            ADMIN_SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(sig, expected_sig):
            return None
            
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)
        
        if time.time() > payload.get("expires_at", 0):
            return None
            
        return payload
    except Exception:
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    token = request.cookies.get("fd_admin_session")
    if not token:
        token = request.cookies.get("fd_user_session")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    return token


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    token = get_token_from_request(request)
    if not token:
        return None
    return verify_token(token)


async def get_current_user(request: Request) -> Dict[str, Any]:
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


async def get_current_admin(request: Request) -> Dict[str, Any]:
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user


def verify_credentials(username: str, password: str) -> bool:
    """Legacy helper for backwards compatibility"""
    u = authenticate_user(username, password)
    return bool(u and u.get("role") == "admin")
