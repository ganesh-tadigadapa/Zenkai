"""Where a student is sent, and what the button says.

One rule, in one place, so the card, the detail page and any future click
tracking cannot disagree:

    a direct destination is used when we have one;
    otherwise the official source, and the button says so.

Nothing here invents a URL. If ``direct_destination_url`` is NULL, the record
genuinely has no established enrol/apply page and the interface admits it.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import (
    DESTINATION_ACTION_BY_TYPE,
    DestinationAction,
    DestinationType,
)
from app.models.opportunity import Opportunity

# Button wording per action. Kept beside the enum it belongs to rather than in
# the frontend, so the API and the UI cannot drift apart.
ACTION_LABELS: dict[DestinationAction, str] = {
    DestinationAction.START_COURSE: "Start course",
    DestinationAction.ENROLL: "Enroll",
    DestinationAction.START_LEARNING: "Start learning",
    DestinationAction.REGISTER_EXAM: "Register for exam",
    DestinationAction.VIEW_CERTIFICATION: "View certification",
    DestinationAction.GET_ACCESS: "Get access",
    DestinationAction.APPLY: "Apply now",
    DestinationAction.REGISTER: "Register",
    DestinationAction.VISIT_SOURCE: "Visit official source",
}


@dataclass
class Destination:
    """The resolved primary call to action."""

    url: str
    type: DestinationType
    action: DestinationAction
    label: str
    #: True when this is the provider's own page rather than an exact
    #: enrol/apply page, so the UI can set expectations honestly.
    is_fallback: bool


def action_for(opportunity: Opportunity) -> DestinationAction:
    """The action a record implies, honouring an explicit override."""
    override = opportunity.destination_action
    if override:
        try:
            return DestinationAction(override)
        except ValueError:
            # An unrecognised override must not break the page; fall through to
            # the type-derived default.
            pass
    return DESTINATION_ACTION_BY_TYPE.get(
        opportunity.opportunity_type, DestinationAction.VISIT_SOURCE
    )


def resolve(opportunity: Opportunity) -> Destination:
    """Pick the URL the primary button points at, and what it should say."""
    direct = (opportunity.direct_destination_url or "").strip()

    if direct:
        action = action_for(opportunity)
        return Destination(
            url=direct,
            type=DestinationType.DIRECT_DESTINATION,
            action=action,
            label=ACTION_LABELS[action],
            is_fallback=False,
        )

    # No established destination. Fall back to the authoritative page and say
    # exactly that, rather than dressing it up as an enrolment link.
    fallback = (opportunity.source_url or opportunity.application_url or "").strip()
    return Destination(
        url=fallback,
        type=DestinationType.OFFICIAL_SOURCE,
        action=DestinationAction.VISIT_SOURCE,
        label=ACTION_LABELS[DestinationAction.VISIT_SOURCE],
        is_fallback=True,
    )


def as_dict(opportunity: Opportunity) -> dict:
    destination = resolve(opportunity)
    return {
        "url": destination.url,
        "type": destination.type.value,
        "action": destination.action.value,
        "label": destination.label,
        "is_fallback": destination.is_fallback,
    }
