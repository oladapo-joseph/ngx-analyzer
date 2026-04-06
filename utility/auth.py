# utility/auth.py — user management and authentication

import sqlite3
import hashlib
import secrets
from dotenv import dotenv_values

_env = dotenv_values(".env")
_DB_PATH = _env.get("DB_PATH", "utility/ngx.sqlite")


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return key.hex(), salt


def init_users_table():
    """Create users table and seed admin account if it doesn't exist."""
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    UNIQUE NOT NULL,
            password_hash TEXT   NOT NULL,
            salt         TEXT    NOT NULL,
            role         TEXT    NOT NULL DEFAULT 'user',
            is_active    INTEGER NOT NULL DEFAULT 1,
            created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Seed admin from env on first run
    admin_user = _env.get("ADMIN_USERNAME", "admin")
    admin_pass = _env.get("ADMIN_PASSWORD", "admin123")
    exists = conn.execute(
        "SELECT id FROM users WHERE username = ?", (admin_user,)
    ).fetchone()
    if not exists:
        pwd_hash, salt = _hash_password(admin_pass)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, 'admin')",
            (admin_user, pwd_hash, salt),
        )
        conn.commit()
    conn.close()


def verify_user(username: str, password: str) -> dict | None:
    """
    Returns {"username": ..., "role": ...} on success, None on failure.
    Returns None if the account is inactive.
    """
    conn = sqlite3.connect(_DB_PATH)
    row = conn.execute(
        "SELECT username, password_hash, salt, role, is_active FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    _, pwd_hash, salt, role, is_active = row
    if not is_active:
        return None
    computed, _ = _hash_password(password, salt)
    if computed == pwd_hash:
        return {"username": username, "role": role}
    return None


def create_user(username: str, password: str, role: str = "user") -> bool:
    """Returns False if username already exists."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        pwd_hash, salt = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, pwd_hash, salt, role),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def list_users() -> list[dict]:
    conn = sqlite3.connect(_DB_PATH)
    rows = conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "username": r[1], "role": r[2], "is_active": bool(r[3]), "created_at": r[4]}
        for r in rows
    ]


def set_user_active(username: str, active: bool):
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "UPDATE users SET is_active = ? WHERE username = ?", (int(active), username)
    )
    conn.commit()
    conn.close()
