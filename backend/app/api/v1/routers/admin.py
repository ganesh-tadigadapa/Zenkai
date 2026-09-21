from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_admin
from app.ingestion.monitoring import monitoring_summary
from app.models.enums import CHECK_FREQUENCY_MINUTES, VerificationStatus
from app.models.opportunity import Opportunity
from app.models.provenance import SourceCheck
from app.models.source import Source
from app.schemas.admin import AdminQueueStats, ReviewDecision, ReviewEdit, ReviewOut
from app.schemas.common import Page
from app.schemas.opportunity import OpportunityAdminOut, OpportunityCreate, OpportunityDetailOut
from app.schemas.source import SourceCheckOut, SourceCreate, SourceOut
from app.services import destination_service
from app.services import opportunity_service as svc
from app.services import review_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _admin_serialize(opportunity: Opportunity) -> OpportunityAdminOut:
    return OpportunityAdminOut.model_validate(
        {
            **opportunity.__dict__,
            "organization": opportunity.organization,
            "source": opportunity.source,
            "days_left": svc.days_left(opportunity),
            "destination": destination_service.as_dict(opportunity),
            "is_saved": False,
            "match": None,
        }
    )


@router.get("/stats", response_model=AdminQueueStats, summary="Review queue counts")
def stats(db: Session = Depends(db_session)):
    return AdminQueueStats(**review_service.queue_stats(db))


@router.get("/queue", response_model=Page[OpportunityAdminOut], summary="Review queue by status")
def queue(
    db: Session = Depends(db_session),
    status_filter: VerificationStatus = Query(
        default=VerificationStatus.NEEDS_REVIEW, alias="status"
    ),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    rows, total = review_service.queue(db, status_filter.value, limit, offset)
    return Page(
        items=[_admin_serialize(r) for r in rows], total=total, limit=limit, offset=offset
    )


def _get(db: Session, opportunity_id: str) -> Opportunity:
    row = db.get(Opportunity, opportunity_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    return row


@router.post("/opportunities/{opportunity_id}/approve", response_model=ReviewOut)
def approve(
    opportunity_id: str, payload: ReviewDecision, db: Session = Depends(db_session)
):
    review = review_service.approve(db, _get(db, opportunity_id), payload.reviewer, payload.notes)
    db.commit()
    return review


@router.post("/opportunities/{opportunity_id}/reject", response_model=ReviewOut)
def reject(opportunity_id: str, payload: ReviewDecision, db: Session = Depends(db_session)):
    review = review_service.reject(db, _get(db, opportunity_id), payload.reviewer, payload.notes)
    db.commit()
    return review


@router.post("/opportunities/{opportunity_id}/edit", response_model=ReviewOut)
def edit(opportunity_id: str, payload: ReviewEdit, db: Session = Depends(db_session)):
    review = review_service.edit(
        db,
        _get(db, opportunity_id),
        payload.reviewer,
        payload.changes.model_dump(exclude_unset=True),
        payload.notes,
    )
    db.commit()
    return review


@router.get("/opportunities/{opportunity_id}/history", response_model=list[ReviewOut])
def history(opportunity_id: str, db: Session = Depends(db_session)):
    return review_service.history(db, opportunity_id)


@router.post(
    "/opportunities",
    response_model=OpportunityDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add an opportunity",
)
def create(payload: OpportunityCreate, db: Session = Depends(db_session)):
    row = svc.create_opportunity(db, payload)
    db.commit()
    db.refresh(row)
    return OpportunityDetailOut.model_validate(
        {
            **row.__dict__,
            "organization": row.organization,
            "source": row.source,
            "days_left": svc.days_left(row),
            "destination": destination_service.as_dict(row),
            "is_saved": False,
            "match": None,
        }
    )


@router.post("/maintenance/expire", summary="Mark opportunities past their deadline as expired")
def expire(db: Session = Depends(db_session)):
    count = svc.expire_passed_deadlines(db)
    db.commit()
    return {"expired": count}


# --- Sources ---------------------------------------------------------------

def _source_payload(source: Source) -> SourceOut:
    return SourceOut.model_validate(
        {
            **source.__dict__,
            "is_authoritative": source.is_authoritative,
            "monitoring_summary": monitoring_summary(source),
        }
    )


@router.get("/sources", response_model=list[SourceOut], summary="The source registry")
def list_sources(db: Session = Depends(db_session)):
    """Registered sources, highest priority first.

    A source that has never been read reports "Not monitored yet." rather than
    a fabricated timestamp.
    """
    sources = db.scalars(
        select(Source).order_by(Source.priority.desc(), Source.name)
    ).all()
    return [_source_payload(source) for source in sources]


@router.get(
    "/sources/{source_id}/checks",
    response_model=list[SourceCheckOut],
    summary="Recent read attempts for a source",
)
def source_checks(source_id: str, db: Session = Depends(db_session), limit: int = 20):
    """Includes the failures — a connector that never works should be visible."""
    return list(
        db.scalars(
            select(SourceCheck)
            .where(SourceCheck.source_id == source_id)
            .order_by(SourceCheck.started_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/sources",
    response_model=SourceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a source for future ingestion",
)
def create_source(payload: SourceCreate, db: Session = Depends(db_session)):
    data = payload.model_dump()
    # Enums come in as members; the columns are strings.
    for key in ("source_type", "authority", "discovery_method", "check_frequency"):
        data[key] = getattr(payload, key).value
    # Derive the interval from the named cadence so the two cannot disagree.
    data["check_frequency_minutes"] = CHECK_FREQUENCY_MINUTES[data["check_frequency"]]
    row = Source(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _source_payload(row)
