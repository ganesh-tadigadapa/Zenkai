from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_optional_user
from app.models.enums import (
    AssessmentType,
    Category,
    CostType,
    CredentialType,
    DeliveryMode,
    ExperienceLevel,
    OpportunityType,
    ProctoredStatus,
    VerificationStatus,
)
from app.models.credential import CredentialDetail
from app.models.opportunity import Opportunity
from app.models.organization import Organization
from app.models.user import User
from app.repositories.opportunity_repository import OpportunityQuery
from app.schemas.common import FacetValue, Page
from app.schemas.opportunity import (
    OpportunityDetailOut,
    OpportunityOut,
    OrganizationOut,
)
from app.services import opportunity_service as svc

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

# What a student may see. REJECTED and EXPIRED are excluded; EXPIRED is filtered
# separately so `include_expired` can bring it back.
PUBLIC_STATUSES = [
    VerificationStatus.CURATED.value,
    VerificationStatus.SOURCE_CHECKED.value,
    VerificationStatus.NEEDS_REVIEW.value,
]


def _serialize(pair, detail: bool = False):
    opportunity, meta = pair
    model = OpportunityDetailOut if detail else OpportunityOut
    return model.model_validate(
        {
            **opportunity.__dict__,
            "organization": opportunity.organization,
            "source": opportunity.source,
            "credential": opportunity.credential,
            **meta,
        }
    )


@router.get("", response_model=Page[OpportunityOut], summary="Browse and search opportunities")
def list_opportunities(
    db: Session = Depends(db_session),
    user: User | None = Depends(get_optional_user),
    q: str | None = Query(default=None, max_length=200, description="Free-text search"),
    category: list[Category] = Query(default=[]),
    type: list[OpportunityType] = Query(default=[]),
    cost: list[CostType] = Query(default=[]),
    organization: list[str] = Query(default=[]),
    skill: list[str] = Query(default=[]),
    credential_type: list[CredentialType] = Query(default=[]),
    specialization: list[str] = Query(default=[], description="Subject area, e.g. aws, kubernetes"),
    assessment: list[AssessmentType] = Query(default=[]),
    proctored: list[ProctoredStatus] = Query(default=[]),
    delivery: list[DeliveryMode] = Query(default=[]),
    level: list[ExperienceLevel] = Query(default=[]),
    issuer: list[str] = Query(default=[]),
    remote: bool | None = Query(default=None),
    location: str | None = Query(default=None, max_length=120),
    free_only: bool = False,
    verified_only: bool = False,
    deadline_within_days: int | None = Query(default=None, ge=0, le=365),
    include_expired: bool = False,
    sort: str = Query(default="deadline", pattern="^(deadline|newest|updated|relevance|title)$"),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = OpportunityQuery(
        search=q,
        categories=[c.value for c in category],
        types=[t.value for t in type],
        cost=[c.value for c in cost],
        organizations=organization,
        skills=skill,
        credential_types=[c.value for c in credential_type],
        specializations=specialization,
        assessment_types=[a.value for a in assessment],
        proctored=[p.value for p in proctored],
        delivery_modes=[d.value for d in delivery],
        experience_levels=[level_value.value for level_value in level],
        issuers=issuer,
        remote=remote,
        location=location,
        free_only=free_only,
        verified_only=verified_only,
        statuses=PUBLIC_STATUSES,
        deadline_within_days=deadline_within_days,
        include_expired=include_expired,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    items, total = svc.list_opportunities(db, query, user)
    return Page(items=[_serialize(p) for p in items], total=total, limit=limit, offset=offset)


@router.get("/facets", response_model=dict[str, list[FacetValue]], summary="Filter facet counts")
def facets(db: Session = Depends(db_session)):
    def counts(column):
        rows = db.execute(
            select(column, func.count(Opportunity.id))
            .where(Opportunity.verification_status.in_(PUBLIC_STATUSES))
            .group_by(column)
        ).all()
        return {str(v): int(c) for v, c in rows if v}

    def to_facets(mapping: dict[str, int]) -> list[FacetValue]:
        return [
            FacetValue(value=v, label=v.replace("_", " ").title(), count=c)
            for v, c in sorted(mapping.items(), key=lambda kv: -kv[1])
        ]

    credential_rows = {
        "credential_type": CredentialDetail.credential_type,
        "assessment": CredentialDetail.assessment_type,
        "proctored": CredentialDetail.proctored_status,
        "delivery": CredentialDetail.delivery_mode,
        "level": CredentialDetail.experience_level,
    }
    credential_facets = {}
    for label, column in credential_rows.items():
        rows = db.execute(
            select(column, func.count(CredentialDetail.opportunity_id))
            .join(Opportunity, Opportunity.id == CredentialDetail.opportunity_id)
            .where(Opportunity.verification_status.in_(PUBLIC_STATUSES))
            .group_by(column)
        ).all()
        credential_facets[label] = to_facets({str(v): int(c) for v, c in rows if v})

    org_rows = db.execute(
        select(Organization.slug, Organization.name, func.count(Opportunity.id))
        .join(Opportunity, Opportunity.organization_id == Organization.id)
        .where(Opportunity.verification_status.in_(PUBLIC_STATUSES))
        .group_by(Organization.slug, Organization.name)
        .order_by(func.count(Opportunity.id).desc())
        .limit(40)
    ).all()

    return {
        **credential_facets,
        "category": to_facets(counts(Opportunity.category)),
        "type": to_facets(counts(Opportunity.opportunity_type)),
        "cost": to_facets(counts(Opportunity.cost_type)),
        "verification_status": to_facets(counts(Opportunity.verification_status)),
        "organization": [
            FacetValue(value=slug, label=name, count=int(count)) for slug, name, count in org_rows
        ],
    }


@router.get("/{identifier}", response_model=OpportunityDetailOut, summary="Opportunity detail")
def get_opportunity(
    identifier: str,
    db: Session = Depends(db_session),
    user: User | None = Depends(get_optional_user),
):
    found = svc.get_detail(db, identifier, user)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    opportunity, _ = found
    if opportunity.verification_status == VerificationStatus.REJECTED.value:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    return _serialize(found, detail=True)


organizations_router = APIRouter(prefix="/organizations", tags=["organizations"])


@organizations_router.get("", response_model=list[OrganizationOut])
def list_organizations(db: Session = Depends(db_session)):
    return list(db.scalars(select(Organization).order_by(Organization.name)).all())


categories_router = APIRouter(prefix="/categories", tags=["categories"])

CATEGORY_META = {
    Category.CERTIFICATIONS: ("Certifications", "Free courses, exams and vouchers that end in a credential.", "award"),
    Category.INTERNSHIPS: ("Internships", "Paid and unpaid roles built for students.", "briefcase"),
    Category.HACKATHONS: ("Hackathons & Competitions", "Build, compete and win — usually in a weekend.", "trophy"),
    Category.PROGRAMS: ("Programs & Fellowships", "Structured cohorts, ambassadorships and fellowships.", "users"),
    Category.TECH_BENEFITS: ("Tech Benefits", "Free and discounted software, cloud credits and AI tools.", "sparkles"),
    Category.SCHOLARSHIPS: ("Scholarships", "Funding for tuition, travel and research.", "graduation-cap"),
}


@categories_router.get("", summary="The six product categories with live counts")
def list_categories(db: Session = Depends(db_session)):
    rows = db.execute(
        select(Opportunity.category, func.count(Opportunity.id))
        .where(Opportunity.verification_status.in_(PUBLIC_STATUSES))
        .group_by(Opportunity.category)
    ).all()
    counts = {c: int(n) for c, n in rows}
    return [
        {
            "slug": category.value,
            "name": name,
            "description": description,
            "icon": icon,
            "count": counts.get(category.value, 0),
        }
        for category, (name, description, icon) in CATEGORY_META.items()
    ]
