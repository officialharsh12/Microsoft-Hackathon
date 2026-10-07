"""
Authentication API — Signup, Login, Session validation.
Uses bcrypt for password hashing and JWT for stateless session tokens.
Stores users in the existing SQLite database.
"""

import json
import datetime
from typing import Optional

import bcrypt
import jwt
from pydantic import BaseModel, EmailStr, field_validator
from fastapi import APIRouter, HTTPException, Header

from app.config import settings
from app.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── JWT helpers ──────────────────────────────────────────────────────────────

JWT_SECRET = settings.AUTH_SECRET
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72  # 3-day session


def _create_token(user_id: int, email: str) -> str:
    """Create a signed JWT token for the user session."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token.")


# ── Password helpers ─────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Hash a password with bcrypt. Never stores plaintext."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── Request / Response schemas ───────────────────────────────────────────────

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v.strip()


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest):
    """
    Register a new user. Password is hashed with bcrypt before storage.
    Creates a default 'demo-org' organization if none exists for the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (body.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Ensure demo org exists
    cursor.execute("SELECT id FROM organizations WHERE slug = 'demo-org' LIMIT 1")
    org_row = cursor.fetchone()
    org_id = org_row["id"] if org_row else 1

    password_hash = _hash_password(body.password)

    cursor.execute(
        """INSERT INTO users (organization_id, email, password_hash, full_name, role, is_active)
           VALUES (?, ?, ?, ?, 'PM', 1)""",
        (org_id, body.email, password_hash, body.full_name),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    token = _create_token(user_id, body.email)
    return AuthResponse(
        token=token,
        user={
            "id": user_id,
            "name": body.full_name,
            "email": body.email,
            "role": "Product Manager",
            "avatar": body.full_name[0].upper() if body.full_name else "U",
        },
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """
    Authenticate user with email + password.
    Returns JWT token for session persistence.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- AUTO-PROVISION DEMO USER ---
    if body.email == "demo@microsoft.com" and body.password == "hackathon2026":
        cursor.execute("SELECT id FROM users WHERE email = ?", (body.email,))
        if not cursor.fetchone():
            # Ensure demo org exists
            cursor.execute("SELECT id FROM organizations WHERE slug = 'demo-org' LIMIT 1")
            org_row = cursor.fetchone()
            org_id = org_row["id"] if org_row else 1
            
            pwd_hash = _hash_password(body.password)
            cursor.execute(
                """INSERT INTO users (organization_id, email, password_hash, full_name, role, is_active)
                   VALUES (?, ?, ?, 'Demo User', 'PM', 1)""",
                (org_id, body.email, pwd_hash),
            )
            conn.commit()
    # --------------------------------

    cursor.execute(
        "SELECT id, email, password_hash, full_name, role FROM users WHERE email = ? AND is_active = 1",
        (body.email,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not row["password_hash"] or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = _create_token(row["id"], row["email"])
    return AuthResponse(
        token=token,
        user={
            "id": row["id"],
            "name": row["full_name"],
            "email": row["email"],
            "role": row["role"] or "Product Manager",
            "avatar": row["full_name"][0].upper() if row["full_name"] else "U",
        },
    )


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Validate the current session token and return user info.
    Used by the frontend to persist sessions on page reload.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    token = authorization.split(" ", 1)[1]
    payload = _verify_token(token)
    user_id = payload.get("sub")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, full_name, role FROM users WHERE id = ? AND is_active = 1",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User not found.")

    return {
        "id": row["id"],
        "name": row["full_name"],
        "email": row["email"],
        "role": row["role"] or "Product Manager",
        "avatar": row["full_name"][0].upper() if row["full_name"] else "U",
    }
