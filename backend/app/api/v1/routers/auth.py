from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import bearer_token, db_session, get_current_user
from app.auth.providers import AuthError
from app.models.user import User
from app.schemas.auth import ChangePasswordIn, LoginIn, SessionOut, SignupIn
from app.schemas.common import Message
from app.schemas.user import ProfileOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_payload(db: Session, user: User, user_agent: str | None = None) -> SessionOut:
    token, session = auth_service.start_session(db, user, user_agent)
    expires_at = session.expires_at.isoformat()
    db.commit()
    db.refresh(user)
    return SessionOut(token=token, expires_at=expires_at, user=ProfileOut.model_validate(user))


@router.post(
    "/signup",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and start a session",
)
def signup(
    payload: SignupIn,
    request: Request,
    db: Session = Depends(db_session),
):
    try:
        user = auth_service.register(db, str(payload.email), payload.name, payload.password)
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _session_payload(db, user, request.headers.get("user-agent"))


@router.post("/login", response_model=SessionOut, summary="Sign in")
def login(payload: LoginIn, request: Request, db: Session = Depends(db_session)):
    try:
        user = auth_service.authenticate(db, str(payload.email), payload.password)
    except AuthError as exc:
        # 401 with a deliberately generic message: the endpoint must not reveal
        # whether the email exists.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    return _session_payload(db, user, request.headers.get("user-agent"))


@router.post("/logout", response_model=Message, summary="End the current session")
def logout(
    db: Session = Depends(db_session),
    token: str | None = Depends(bearer_token),
):
    ended = auth_service.end_session(db, token or "")
    db.commit()
    return Message(detail="Signed out." if ended else "No active session.")


@router.get("/me", response_model=ProfileOut, summary="The signed-in user")
def me(user: User = Depends(get_current_user)):
    return user


@router.post(
    "/change-password",
    response_model=SessionOut,
    summary="Change your password and re-issue the session",
)
def change_password(
    payload: ChangePasswordIn,
    request: Request,
    db: Session = Depends(db_session),
    user: User = Depends(get_current_user),
):
    try:
        auth_service.change_password(db, user, payload.current_password, payload.new_password)
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    # A password change signs out every device, including this one, and then
    # issues a fresh session so the person who just changed it stays signed in.
    auth_service.end_all_sessions(db, user)
    return _session_payload(db, user, request.headers.get("user-agent"))
