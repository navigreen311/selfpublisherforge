"""Helper utilities for the auth module: token generation, email tokens, TOTP helpers."""

import hashlib
import hmac
import secrets
import struct
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Opaque token helpers (email verification, password reset)
# ---------------------------------------------------------------------------

def generate_token(nbytes: int = 32) -> str:
    """Generate a cryptographically-secure URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def generate_token_hash(token: str) -> str:
    """Return a SHA-256 hex digest of *token* for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def token_expiry(hours: int = 24) -> datetime:
    """Return a UTC datetime *hours* from now."""
    return datetime.now(UTC) + timedelta(hours=hours)


# ---------------------------------------------------------------------------
# Backup codes
# ---------------------------------------------------------------------------

def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate a list of one-time-use backup codes (8-char hex strings)."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


# ---------------------------------------------------------------------------
# TOTP (RFC 6238) — pure-Python implementation to avoid extra dependencies
# ---------------------------------------------------------------------------

_TOTP_DIGITS = 6
_TOTP_PERIOD = 30
_TOTP_SKEW = 1  # allow +/- 1 period


def generate_totp_secret(nbytes: int = 20) -> str:
    """Generate a random base32-encoded TOTP secret."""
    import base64
    raw = secrets.token_bytes(nbytes)
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def _hotp(secret_b32: str, counter: int) -> str:
    """Compute a 6-digit HOTP value (RFC 4226)."""
    import base64
    # Pad the base32 secret
    padded = secret_b32 + "=" * (-len(secret_b32) % 8)
    key = base64.b32decode(padded.upper())
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    truncated = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(truncated % (10 ** _TOTP_DIGITS)).zfill(_TOTP_DIGITS)


def verify_totp(secret_b32: str, code: str) -> bool:
    """Verify a TOTP code with +/- 1 period skew tolerance."""
    now = int(time.time())
    for offset in range(-_TOTP_SKEW, _TOTP_SKEW + 1):
        counter = (now // _TOTP_PERIOD) + offset
        if hmac.compare_digest(_hotp(secret_b32, counter), code):
            return True
    return False


def build_totp_uri(secret: str, email: str, issuer: str | None = None) -> str:
    """Build an otpauth:// URI for QR-code provisioning."""
    issuer = issuer or settings.APP_NAME
    label = quote(f"{issuer}:{email}", safe="")
    params = f"secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={_TOTP_DIGITS}&period={_TOTP_PERIOD}"
    return f"otpauth://totp/{label}?{params}"
