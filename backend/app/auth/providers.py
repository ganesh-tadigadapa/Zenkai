"""Identity provider contract.

Only the password provider ships today. The seam exists so GitHub, Google or a
magic-link provider can be added without touching the session layer, the
routers or anything downstream: each one only has to turn whatever it knows
into a ``ProviderIdentity``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ProviderIdentity:
    """A verified identity, however it was established."""

    email: str
    name: str
    provider: str
    # Stable id at the provider, for accounts with no usable email.
    provider_account_id: str | None = None


@runtime_checkable
class IdentityProvider(Protocol):
    """Turns provider-specific input into a verified identity.

    Implementations must raise on failure rather than returning a partial
    identity: a provider that cannot prove who someone is has not authenticated
    them.
    """

    name: str

    def authenticate(self, **credentials: object) -> ProviderIdentity: ...


class AuthError(Exception):
    """Authentication failed. The message is safe to show a user."""


class PasswordProvider:
    """Email and password, verified against the local user table.

    Deliberately gives the same error for an unknown email and a wrong
    password, so the endpoint cannot be used to discover which addresses have
    accounts.
    """

    name = "password"

    GENERIC_FAILURE = "Email or password is incorrect."
