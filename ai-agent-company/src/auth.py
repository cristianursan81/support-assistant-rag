"""Authentication — JWT tokens + password hashing."""
import os
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt

JWT_SECRET = os.getenv("JWT_SECRET", "cambia-esto-en-produccion-ahora-mismo")
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# ---------------------------------------------------------------------------
# Password helpers (bcrypt, no passlib dependency)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Minimal HS256 JWT (no cryptography native dep needed)
# ---------------------------------------------------------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_access_token(user_id: int, workspace_id: int) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    exp = int((datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp())
    payload = _b64url(json.dumps({"sub": str(user_id), "ws": workspace_id, "exp": exp}).encode())
    sig_input = f"{header}.{payload}".encode()
    sig = hmac.new(JWT_SECRET.encode(), sig_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64url(sig)}"


def decode_token(token: str) -> Optional[dict]:
    """Returns payload dict or None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload_b64, sig_b64 = parts
        # Verify signature
        expected = hmac.new(
            JWT_SECRET.encode(),
            f"{header}.{payload_b64}".encode(),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
            return None
        data = json.loads(_b64url_decode(payload_b64))
        # Check expiry
        if data.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            return None
        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_user_by_email(email: str, db):
    from src.models import User
    return db.query(User).filter(User.email == email.lower()).first()


def authenticate_user(email: str, password: str, db):
    user = get_user_by_email(email, db)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def register_user(email: str, password: str, full_name: str, workspace_id: int, db):
    from src.models import User
    if len(password) < 8:
        raise ValueError("La contraseña debe tener mínimo 8 caracteres.")
    if get_user_by_email(email, db):
        raise ValueError("Este email ya está registrado.")
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        workspace_id=workspace_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
