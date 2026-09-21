from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_optional_user
from app.api.v1.routers.opportunities import _serialize
from app.models.user import User
from app.schemas.opportunity import OpportunityOut
from app.services import deadline_service

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


class DeadlinesOut(BaseModel):
    today: list[OpportunityOut]
    this_week: list[OpportunityOut]
    upcoming: list[OpportunityOut]
    total: int


@router.get("", response_model=DeadlinesOut, summary="Deadlines bucketed by urgency")
def deadlines(
    db: Session = Depends(db_session),
    user: User | None = Depends(get_optional_user),
    horizon_days: int = Query(default=60, ge=1, le=365),
    saved_only: bool = False,
):
    buckets = deadline_service.grouped(db, user, horizon_days, saved_only)
    out = {key: [_serialize(p) for p in value] for key, value in buckets.items()}
    return DeadlinesOut(**out, total=sum(len(v) for v in out.values()))
