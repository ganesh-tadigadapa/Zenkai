"""Password hashing and session tokens.

Two deliberate choices:

* **Argon2id** for passwords, via ``argon2-cffi``. It is the current password
  hashing recommendation, and the library handles salting and parameter
  encoding, so nothing here rolls its own crypto.
* **Opaque, database-backed session tokens** rather than JWTs. A session can be
  revoked the instant someone signs out, there is no signing secret to rotate or
  leak, and we already have a database. JWTs would buy statelessness we do not
  need at this size and cost us revocation.

The token the client holds is random and never stored; only its SHA-256 digest
is persisted, so a database leak does not hand over live sessions.
"""
from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Defaults follow argon2-cffi's recommended profile.
_hasher = PasswordHasher()

# 32 bytes of entropy, URL-safe. Long enough that guessing is not a threat model.
TOKEN_BYTES = 32

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 200  # argon2 is not length-limited, but unbounded input is a DoS vector


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Constant-time-ish verification that never raises on bad input.

    Returns False for users with no password set (an OAuth-only account, once
    that exists) rather than letting a None hash blow up the login path.
    """
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when the stored hash uses outdated parameters and should be upgraded."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def generate_session_token() -> str:
    """The secret handed to the client. Never stored."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """What we persist.

    A fast hash is correct here, unlike for passwords: the token already has
    full entropy, so there is nothing to brute-force and no reason to make
    lookups expensive.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def password_problems(password: str) -> list[str]:
    """Validation with readable reasons, so the UI can show what to fix."""
    problems: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"Use at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > MAX_PASSWORD_LENGTH:
        problems.append(f"Keep it under {MAX_PASSWORD_LENGTH} characters.")
    if password.strip() != password:
        problems.append("Remove leading or trailing spaces.")
    if password.isdigit():
        problems.append("Use more than just numbers.")
    return problems
