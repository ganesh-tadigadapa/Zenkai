from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_optional_user
from app.api.v1.routers.opportunities import _serialize
from app.models.user import User
from app.schemas.common import StatsOut
from app.schemas.opportunity import OpportunityOut
from app.services import opportunity_service as svc

router = APIRouter(tags=["dashboard"])


@router.get("/stats", response_model=StatsOut, summary="Dashboard headline metrics")
def stats(db: Session = Depends(db_session), user: User | None = Depends(get_optional_user)):
    return StatsOut(**svc.stats(db, user))


@router.get(
    "/dashboard",
    summary="Every dashboard shelf in one round trip",
    response_model=dict[str, object],
)
def dashboard(
    db: Session = Depends(db_session),
    user: User | None = Depends(get_optional_user),
    limit: int = Query(default=6, ge=1, le=24),
):
    def shelf(pairs) -> list[OpportunityOut]:
        return [_serialize(p) for p in pairs]

    return {
        "stats": svc.stats(db, user),
        "recommended": shelf(svc.recommended(db, user, limit)),
        "new_today": shelf(svc.new_today(db, user, limit)),
        "closing_soon": shelf(svc.closing_soon(db, user, limit)),
        "recently_updated": shelf(svc.recently_updated(db, user, limit)),
        "has_preferences": bool(user and user.preferences),
    }


@router.get(
    "/recommendations",
    response_model=list[OpportunityOut],
    summary="Rule-based recommendations for the current user",
)
def recommendations(
    db: Session = Depends(db_session),
    user: User | None = Depends(get_optional_user),
    limit: int = Query(default=12, ge=1, le=50),
):
    return [_serialize(p) for p in svc.recommended(db, user, limit)]
