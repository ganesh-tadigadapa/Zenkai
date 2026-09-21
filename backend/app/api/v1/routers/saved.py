from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.api.v1.routers.opportunities import _serialize
from app.models.user import User
from app.schemas.opportunity import OpportunityOut
from app.services import saved_service

router = APIRouter(prefix="/saved", tags=["saved"])


class SaveIn(BaseModel):
    opportunity_id: str
    notes: str | None = None


class SavedListOut(BaseModel):
    active: list[OpportunityOut]
    expired: list[OpportunityOut]
    total: int


@router.get("", response_model=SavedListOut, summary="Saved opportunities, split by status")
def list_saved(db: Session = Depends(db_session), user: User = Depends(get_current_user)):
    result = saved_service.list_saved(db, user)
    active = [_serialize(p) for p in result["active"]]
    expired = [_serialize(p) for p in result["expired"]]
    return SavedListOut(active=active, expired=expired, total=len(active) + len(expired))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Save an opportunity")
def save(
    payload: SaveIn,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    try:
        created = saved_service.save(db, user, payload.opportunity_id, payload.notes)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
    db.commit()
    return {"saved": True, "created": created}


@router.delete("/{opportunity_id}", summary="Remove a saved opportunity")
def unsave(
    opportunity_id: str,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    removed = saved_service.unsave(db, user, opportunity_id)
    db.commit()
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not saved")
    return {"saved": False}
