"""Idempotent Zenkai database seeder.

    python -m app.seed.run          # create tables and load the catalogue
    python -m app.seed.run --reset  # drop everything first

Re-running without --reset is safe: records are matched on their content hash.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import Base, SessionLocal, create_all, engine
from app.core.security import hash_password
from app.models.enums import (
    DataOrigin,
    RemotePreference,
    VerificationMethod,
    VerificationStatus,
)
from app.models.opportunity import Opportunity, content_fingerprint
from app.models.source import Source
from app.models.user import User, UserPreferences
from app.models.credential import CredentialDetail
from app.models.enums import CHECK_FREQUENCY_MINUTES, UrlCheckStatus
from app.seed.data import ALL_SEEDS
from app.seed.credentials import CREDENTIAL_FACTS
from app.seed.destinations import BLOCKED_TO_BOTS, NO_DIRECT_DESTINATION, URL_FIXES
from app.seed.sources import SOURCES
from app.services.opportunity_service import get_or_create_organization, unique_slug

SEED_CURATOR = "zenkai-curation"

DEMO_STUDENT = dict(
    email="student@zenkai.dev",
    name="Aarav Sharma",
    prefs=dict(
        degree="B.Tech",
        field_of_study="Computer Science",
        year="3rd Year",
        country="India",
        location="Bengaluru, India",
        remote_preference=RemotePreference.ANY.value,
        skills=["Python", "JavaScript", "React", "Docker", "AWS", "SQL"],
        interests=["Cloud", "DevOps", "AI", "Web Development", "Open Source"],
        preferred_categories=["tech_benefits", "internships", "certifications", "hackathons"],
    ),
)

ADMIN_USER = dict(email="reviewer@zenkai.dev", name="Review Team", is_admin=True)


def seed_users(db) -> None:
    """Create the two demo accounts.

    Both get a real password so the login flow can actually be exercised, and
    both are flagged ``is_demo`` so the interface can label them honestly rather
    than passing them off as ordinary accounts. The passwords come from
    settings, so a deployment can override them — and should.
    """
    student = db.scalars(select(User).where(User.email == DEMO_STUDENT["email"])).first()
    if student is None:
        student = User(
            email=DEMO_STUDENT["email"],
            name=DEMO_STUDENT["name"],
            password_hash=hash_password(settings.DEMO_USER_PASSWORD),
            is_demo=True,
        )
        db.add(student)
        db.flush()
    if student.preferences is None:
        db.add(UserPreferences(user_id=student.id, **DEMO_STUDENT["prefs"]))

    admin = db.scalars(select(User).where(User.email == ADMIN_USER["email"])).first()
    if admin is None:
        db.add(
            User(
                **ADMIN_USER,
                password_hash=hash_password(settings.DEMO_ADMIN_PASSWORD),
                is_demo=True,
            )
        )


def seed_sources(db) -> dict[str, Source]:
    by_name: dict[str, Source] = {}
    for spec in SOURCES:
        existing = db.scalars(select(Source).where(Source.name == spec["name"])).first()
        if existing is None:
            payload = dict(spec)
            # Derive the interval from the named cadence, so the two cannot
            # disagree. The monitoring timestamps stay NULL: nothing has been
            # checked yet, and saying otherwise would be a fabricated timestamp.
            payload["check_frequency_minutes"] = CHECK_FREQUENCY_MINUTES[
                payload.get("check_frequency", "normal")
            ]
            existing = Source(**payload)
            db.add(existing)
            db.flush()
        by_name[spec["name"]] = existing
    return by_name


def seed_credentials(db) -> int:
    """Attach credential facts to the certification records.

    Only the facts in app/seed/credentials.py are written. Everything else
    keeps its UNKNOWN default, which is the honest answer for a field no
    official page states.
    """
    from app.models.opportunity import Opportunity

    written = 0
    for title, facts in CREDENTIAL_FACTS.items():
        opportunity = db.scalars(select(Opportunity).where(Opportunity.title == title)).first()
        if opportunity is None or opportunity.credential is not None:
            continue

        detail = CredentialDetail(
            opportunity_id=opportunity.id,
            credential_type=facts["credential_type"].value,
            specializations=[s.value for s in facts.get("specializations", [])],
            issuer=facts.get("issuer"),
            exam_code=facts.get("exam_code"),
            validity_months=facts.get("validity_months"),
        )
        for key, column in (
            ("assessment_type", "assessment_type"),
            ("proctored", "proctored_status"),
            ("delivery_mode", "delivery_mode"),
            ("experience_level", "experience_level"),
        ):
            if key in facts:
                setattr(detail, column, facts[key].value)

        # A stated cost on the credential overrides the catalogue default:
        # free training behind a paid exam is EXAM_FEE, not FREE.
        if "cost" in facts:
            opportunity.cost_type = facts["cost"].value

        db.add(detail)
        written += 1
    db.flush()
    return written


# Every seeded record was entered by hand during curation, so all of them are
# attributed to the manual source. Attributing them to a fetching source would
# imply the ingestion pipeline produced them, which it did not.
SEED_SOURCE_NAME = "Manual editorial submissions"


def seed_opportunities(db, sources: dict[str, Source]) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    created = skipped = 0

    for index, spec in enumerate(ALL_SEEDS):
        org = get_or_create_organization(db, spec["org"], spec.get("org_url"))
        fingerprint = content_fingerprint(
            spec["title"], org.name, URL_FIXES.get(spec["title"], {}).get("url", spec["url"])
        )
        if db.scalars(
            select(Opportunity).where(Opportunity.content_hash == fingerprint)
        ).first():
            skipped += 1
            continue

        deadline = None
        if spec.get("deadline_days") is not None:
            deadline = now + timedelta(days=int(spec["deadline_days"]))

        # Apply the link audit's findings. A record's catalogue URL is its
        # direct destination unless the audit found it to be a hub, a listing
        # or a search page — those fall back to the official source instead.
        title = spec["title"]
        fix = URL_FIXES.get(title, {})
        apply_url = fix.get("url", spec["url"])
        source_url = fix.get("source_url", spec["source_url"])
        direct_url = None if title in NO_DIRECT_DESTINATION else apply_url

        if title in BLOCKED_TO_BOTS:
            url_status = UrlCheckStatus.BLOCKED.value
        elif title in NO_DIRECT_DESTINATION:
            url_status = UrlCheckStatus.UNCHECKED.value
        else:
            url_status = UrlCheckStatus.OK.value

        status = spec.get("status", VerificationStatus.NEEDS_REVIEW.value)
        # Stagger discovery times so "new today" and "recently updated" are meaningful.
        discovered = now - timedelta(hours=index * 5 % 400)

        row = Opportunity(
            title=spec["title"],
            slug=unique_slug(db, spec["title"]),
            organization_id=org.id,
            source_id=sources[SEED_SOURCE_NAME].id if SEED_SOURCE_NAME in sources else None,
            category=spec["category"],
            opportunity_type=spec["type"],
            summary=spec["summary"],
            description=spec["description"],
            eligibility=spec.get("eligibility"),
            who_can_apply=spec.get("who_can_apply", []),
            location=spec.get("location", "Global"),
            is_remote=spec.get("remote", True),
            cost_type=spec.get("cost", "free"),
            deadline=deadline,
            is_rolling=spec.get("rolling", False),
            deadline_is_estimated=bool(spec.get("estimated", False)),
            application_url=apply_url,
            source_url=source_url,
            direct_destination_url=direct_url,
            last_url_checked_at=now,
            url_check_status=url_status,
            skills=spec.get("skills", []),
            tags=spec.get("tags", []),
            benefits=spec.get("benefits", []),
            verification_status=status,
            # Curated records were written by a person against the official
            # page; nothing else has looked at them. Records still needing a
            # reviewer carry no method and no reviewer stamp.
            verification_method=(
                VerificationMethod.CURATION.value
                if status == VerificationStatus.CURATED.value
                else VerificationMethod.NONE.value
            ),
            data_origin=DataOrigin.SEED.value,
            confidence=0.8 if status == VerificationStatus.CURATED.value else 0.5,
            verified_at=now if status == VerificationStatus.CURATED.value else None,
            verified_by=SEED_CURATOR if status == VerificationStatus.CURATED.value else None,
            last_checked_at=now - timedelta(hours=index % 18),
            discovered_at=discovered,
            content_hash=fingerprint,
        )
        db.add(row)
        created += 1

    db.flush()
    return created, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the Zenkai database")
    parser.add_argument("--reset", action="store_true", help="drop all tables first")
    args = parser.parse_args(argv)

    if args.reset:
        Base.metadata.drop_all(bind=engine)
    create_all()

    with SessionLocal() as db:
        seed_users(db)
        sources = seed_sources(db)
        created, skipped = seed_opportunities(db, sources)
        credentials = seed_credentials(db)
        db.commit()

    with SessionLocal() as db:
        from app.models.opportunity import Opportunity as _Opportunity

        direct = db.scalar(
            select(func.count())
            .select_from(_Opportunity)
            .where(_Opportunity.direct_destination_url.is_not(None))
        )
        total = db.scalar(select(func.count()).select_from(_Opportunity))

    print(f"Seeded {created} opportunities ({skipped} already present), {len(SOURCES)} sources.")
    print(f"Direct destinations: {direct}/{total} · {total - direct} fall back to official source.")
    print(f"Credential details:  {credentials} certification records.")
    print()
    print("Demo accounts (change the passwords before any public deployment):")
    print(f"  student  {settings.DEMO_USER_EMAIL}  /  {settings.DEMO_USER_PASSWORD}")
    print(f"  reviewer {settings.DEMO_ADMIN_EMAIL}  /  {settings.DEMO_ADMIN_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
