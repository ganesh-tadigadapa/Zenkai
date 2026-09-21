"""Test fixtures.

Every test runs against a fresh in-memory SQLite database with the dependency
override applied, so tests never touch the developer's local database.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set, not setdefault: tests must be hermetic even when the developer has a
# real DATABASE_URL exported in their shell, or importing the app would create
# tables in their PostgreSQL instance.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ADMIN_TOKEN"] = "test-admin-token"
os.environ["ENV"] = "test"
# Must match the `student` fixture below, or identity resolution 503s.
os.environ["DEMO_USER_EMAIL"] = "student@zenkai.dev"

from app.api.deps import db_session  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import (  # noqa: E402
    Category,
    CostType,
    DataOrigin,
    OpportunityType,
    RemotePreference,
    VerificationStatus,
)
from app.models.opportunity import Opportunity, content_fingerprint  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.user import User, UserPreferences  # noqa: E402
from app.services import auth_service  # noqa: E402

ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}


class FakeFetcher:
    """Serves canned feed bodies, so no test ever touches the live web.

    Mirrors PoliteFetcher's surface: `get` returns a FetchedDocument or raises
    whatever the fixture says the host would have done.
    """

    def __init__(self, responses: dict[str, object]) -> None:
        #: url -> body string, or an exception instance to raise.
        self.responses = responses
        self.requested: list[str] = []

    def may_fetch(self, url: str) -> tuple[bool, str]:
        return True, "fixture"

    def get(self, url: str):
        from datetime import datetime, timezone

        from app.ingestion.fetcher import FetchedDocument

        self.requested.append(url)
        if url not in self.responses:
            from app.ingestion.fetcher import FetchFailed

            raise FetchFailed(f"no fixture registered for {url}")
        canned = self.responses[url]
        if isinstance(canned, Exception):
            raise canned
        return FetchedDocument(
            url=url,
            final_url=url,
            status_code=200,
            content_type="application/rss+xml",
            body=str(canned),
            retrieved_at=datetime.now(timezone.utc),
        )

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any test that tries to make a real HTTP request.

    Discovery talks to the outside world, so it is easy to write a test that
    silently depends on a live site being up and behaving. Tests must use
    FakeFetcher or a fixture body instead; this turns an accidental network
    call into an immediate, obvious failure.
    """
    import httpx

    def refuse(self, request, *args, **kwargs):
        raise AssertionError(
            f"a test attempted a real HTTP request to {request.url} — inject "
            "FakeFetcher instead of depending on a live site"
        )

    # Patch the real network transport only. TestClient drives the app through
    # ASGITransport in-process, which must keep working.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", refuse)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db(engine):
    Session = sessionmaker(bind=engine, autoflush=False, future=True)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    app.dependency_overrides[db_session] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Factories ---------------------------------------------------------------

def make_org(db, name="Example Org") -> Organization:
    """Get-or-create, so several opportunities can share one organisation."""
    from sqlalchemy import select

    slug = name.lower().replace(" ", "-")
    org = db.scalars(select(Organization).where(Organization.slug == slug)).first()
    if org is None:
        org = Organization(name=name, slug=slug)
        db.add(org)
        db.flush()
    return org


def make_opportunity(
    db,
    *,
    title="Example Opportunity",
    org=None,
    category=Category.TECH_BENEFITS,
    opportunity_type=OpportunityType.SOFTWARE,
    cost=CostType.FREE,
    deadline_days: int | None = 10,
    is_remote=True,
    location="Global",
    status=VerificationStatus.CURATED,
    skills=None,
    tags=None,
    is_rolling=False,
    confidence=0.9,
) -> Opportunity:
    org = org or make_org(db)
    # Accept plain strings as well as enum members, so tests can read naturally.
    category = Category(category) if isinstance(category, str) else category
    opportunity_type = (
        OpportunityType(opportunity_type) if isinstance(opportunity_type, str) else opportunity_type
    )
    cost = CostType(cost) if isinstance(cost, str) else cost
    status = VerificationStatus(status) if isinstance(status, str) else status
    deadline = (
        datetime.now(timezone.utc) + timedelta(days=deadline_days)
        if deadline_days is not None
        else None
    )
    url = f"https://example.com/{title.lower().replace(' ', '-')}"
    row = Opportunity(
        title=title,
        slug=title.lower().replace(" ", "-"),
        organization_id=org.id,
        category=category.value,
        opportunity_type=opportunity_type.value,
        summary=f"{title} summary for testing purposes.",
        description=f"{title} full description, long enough to be realistic content.",
        eligibility="Open to enrolled students.",
        location=location,
        is_remote=is_remote,
        cost_type=cost.value,
        deadline=deadline,
        is_rolling=is_rolling,
        application_url=url,
        source_url=url,
        skills=skills or ["Python"],
        tags=tags or ["testing"],
        benefits=["A benefit"],
        verification_status=status.value,
        data_origin=DataOrigin.SEED.value,
        confidence=confidence,
        content_hash=content_fingerprint(title, org.name, url),
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def student(db, client) -> User:
    """A signed-in student.

    Requesting this fixture alongside `client` authenticates that client, so
    tests exercise the real Bearer-token path rather than an implicit identity.
    A test that wants an anonymous caller simply does not request it.
    """
    user = User(
        email="student@zenkai.dev",
        name="Test Student",
        password_hash=hash_password("test-password-123"),
    )
    db.add(user)
    db.flush()
    db.add(
        UserPreferences(
            user_id=user.id,
            degree="B.Tech",
            field_of_study="Computer Science",
            year="3rd Year",
            location="Bengaluru, India",
            remote_preference=RemotePreference.ANY.value,
            skills=["Python", "AWS"],
            interests=["Cloud", "AI"],
            preferred_categories=[Category.TECH_BENEFITS.value],
        )
    )
    db.flush()

    token, _ = auth_service.start_session(db, user)
    client.headers["Authorization"] = f"Bearer {token}"
    return user


@pytest.fixture()
def admin_user(db, client) -> User:
    """A signed-in reviewer, for tests that go through the admin UI path."""
    user = User(
        email="reviewer@zenkai.dev",
        name="Test Reviewer",
        is_admin=True,
        password_hash=hash_password("test-password-123"),
    )
    db.add(user)
    db.flush()
    token, _ = auth_service.start_session(db, user)
    client.headers["Authorization"] = f"Bearer {token}"
    return user
