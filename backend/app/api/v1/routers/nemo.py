from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_optional_user
from app.api.v1.routers.opportunities import PUBLIC_STATUSES, _serialize
from app.models.user import User
from app.schemas.opportunity import OpportunityOut
from app.services import nemo

router = APIRouter(prefix="/nemo", tags=["nemo"])


class NemoMessage(BaseModel):
    message: str = Field(default="", max_length=500)


class NemoReplyOut(BaseModel):
    reply: str
    opportunities: list[OpportunityOut] = []
    browse_url: str | None = None
    suggestions: list[str] = []


@router.post("/chat", response_model=NemoReplyOut, summary="Ask Nemo, the opportunity guide")
def chat(
    body: NemoMessage,
    db: Session = Depends(db_session),
    user: User | None = Depends(get_optional_user),
) -> NemoReplyOut:
    """One turn of conversation. Stateless: every message stands on its own.

    An empty message returns Nemo's introduction and starter questions.
    """
    answer = nemo.respond(db, body.message, user, PUBLIC_STATUSES)
    return NemoReplyOut(
        reply=answer.text,
        opportunities=[_serialize(pair) for pair in answer.results],
        browse_url=answer.browse_url,
        suggestions=answer.suggestions,
    )
