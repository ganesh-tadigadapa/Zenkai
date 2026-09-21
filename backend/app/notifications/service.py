"""Notification foundation.

The MVP persists notifications and exposes the channel interface; no channel
actually sends yet. ``NotificationService.dispatch`` is the single seam a real
email/push/Telegram provider plugs into.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import NotificationChannel, NotificationStatus
from app.models.interaction import Notification
from app.models.opportunity import Opportunity
from app.models.user import User
from app.services.matching import score_opportunity

logger = logging.getLogger(__name__)

# Only surface opportunities a student would plausibly care about.
NOTIFY_MATCH_THRESHOLD = 70


class NotificationChannelHandler(ABC):
    channel: NotificationChannel

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """Return True on successful delivery."""


class LogChannel(NotificationChannelHandler):
    """Development sink: records the intent to send, sends nothing."""

    channel = NotificationChannel.BROWSER

    def send(self, notification: Notification) -> bool:
        logger.info("[notification:%s] %s", notification.channel, notification.title)
        return True


class NotificationService:
    def __init__(self, handlers: dict[str, NotificationChannelHandler] | None = None) -> None:
        self.handlers = handlers or {NotificationChannel.BROWSER.value: LogChannel()}

    def queue(
        self,
        db: Session,
        user: User,
        title: str,
        body: str | None = None,
        channel: NotificationChannel = NotificationChannel.BROWSER,
        opportunity: Opportunity | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user.id,
            opportunity_id=opportunity.id if opportunity else None,
            channel=channel.value,
            title=title,
            body=body,
        )
        db.add(notification)
        db.flush()
        return notification

    def dispatch(self, db: Session, notification: Notification) -> bool:
        handler = self.handlers.get(notification.channel)
        if handler is None:
            notification.status = NotificationStatus.FAILED.value
            return False
        ok = handler.send(notification)
        notification.status = (
            NotificationStatus.SENT.value if ok else NotificationStatus.FAILED.value
        )
        notification.sent_at = datetime.now(timezone.utc) if ok else None
        db.flush()
        return ok

    def queue_matches(self, db: Session, user: User, opportunities: list[Opportunity]) -> list[Notification]:
        """Queue one notification per strongly matching opportunity."""
        if user.preferences is None:
            return []
        queued = []
        for opportunity in opportunities:
            match = score_opportunity(opportunity, user.preferences)
            if match.score >= NOTIFY_MATCH_THRESHOLD:
                queued.append(
                    self.queue(
                        db,
                        user,
                        title=f"{match.score}% match: {opportunity.title}",
                        body=opportunity.summary,
                        opportunity=opportunity,
                    )
                )
        return queued
