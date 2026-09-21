from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewAction, VerificationStatus
from app.schemas.opportunity import OpportunityUpdate


class ReviewDecision(BaseModel):
    reviewer: str = Field(default="admin", max_length=160)
    notes: str | None = None


class ReviewEdit(ReviewDecision):
    changes: OpportunityUpdate


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    reviewer: str
    action: ReviewAction
    previous_status: VerificationStatus | None
    new_status: VerificationStatus | None
    notes: str | None
    created_at: datetime


class AdminQueueStats(BaseModel):
    pending: int
    verified: int
    rejected: int
    expired: int
