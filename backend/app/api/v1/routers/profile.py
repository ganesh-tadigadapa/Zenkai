from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models.user import User, UserPreferences
from app.schemas.user import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut, summary="Current user and preferences")
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.put("", response_model=ProfileOut, summary="Update profile and matching preferences")
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        user.email = str(payload.email)

    if payload.preferences is not None:
        prefs = user.preferences or UserPreferences(user_id=user.id)
        data = payload.preferences.model_dump()
        data["preferred_categories"] = [
            c.value if hasattr(c, "value") else c for c in data.get("preferred_categories", [])
        ]
        data["remote_preference"] = (
            data["remote_preference"].value
            if hasattr(data["remote_preference"], "value")
            else data["remote_preference"]
        )
        for key, value in data.items():
            setattr(prefs, key, value)
        db.add(prefs)
        user.preferences = prefs

    db.commit()
    db.refresh(user)
    return user
