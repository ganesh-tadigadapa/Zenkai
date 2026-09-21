"""Rule-based opportunity matching.

This is deliberately NOT machine learning. Every point awarded is explainable
and is surfaced to the student as a reason string. The interface
(``score_opportunity`` returning a ``MatchResult``) is what a future learned
ranker would implement, so the call sites do not change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.enums import CostType, RemotePreference
from app.models.opportunity import Opportunity
from app.models.user import UserPreferences

# Weights sum to 100 when every signal fires.
W_CATEGORY = 30
W_INTERESTS = 25
W_SKILLS = 20
W_ELIGIBILITY = 10
W_DEADLINE = 10
W_COST = 5


@dataclass
class MatchReason:
    label: str
    detail: str
    points: int


@dataclass
class MatchResult:
    score: int
    reasons: list[MatchReason] = field(default_factory=list)


def _normalize(values: list[str] | None) -> set[str]:
    return {v.strip().lower() for v in (values or []) if v and v.strip()}


def _overlap(a: set[str], b: set[str]) -> set[str]:
    """Case-insensitive overlap that also catches substring matches ('AI' in 'AI Tools')."""
    hits = a & b
    for item in a:
        for other in b:
            if item != other and (item in other or other in item) and len(item) > 2:
                hits.add(other)
    return hits


def score_opportunity(
    opportunity: Opportunity,
    prefs: UserPreferences | None,
    now: datetime | None = None,
) -> MatchResult:
    """Return a 0-100 match score plus the reasons behind it."""
    if prefs is None:
        return MatchResult(score=0, reasons=[])

    now = now or datetime.now(timezone.utc)
    reasons: list[MatchReason] = []
    score = 0

    preferred = _normalize([str(c) for c in (prefs.preferred_categories or [])])
    if preferred and opportunity.category in preferred:
        score += W_CATEGORY
        reasons.append(
            MatchReason(
                "Category",
                f"You're looking for {opportunity.category.replace('_', ' ')}.",
                W_CATEGORY,
            )
        )

    interests = _normalize(prefs.interests)
    opp_topics = _normalize(list(opportunity.tags or []) + list(opportunity.skills or []))
    interest_hits = _overlap(interests, opp_topics)
    if interest_hits:
        pts = min(W_INTERESTS, 10 + 5 * len(interest_hits))
        score += pts
        sample = ", ".join(sorted(interest_hits)[:3])
        reasons.append(MatchReason("Interests", f"Matches your interest in {sample}.", pts))

    skills = _normalize(prefs.skills)
    skill_hits = _overlap(skills, _normalize(list(opportunity.skills or [])))
    if skill_hits:
        pts = min(W_SKILLS, 8 + 4 * len(skill_hits))
        score += pts
        sample = ", ".join(sorted(skill_hits)[:3])
        reasons.append(MatchReason("Skills", f"Uses skills you listed: {sample}.", pts))

    # Location / remote fit.
    if opportunity.is_remote and prefs.remote_preference in (
        RemotePreference.REMOTE.value,
        RemotePreference.ANY.value,
    ):
        score += W_ELIGIBILITY
        reasons.append(MatchReason("Location", "Remote-friendly, which fits your preference.", W_ELIGIBILITY))
    elif prefs.location and opportunity.location and prefs.location.lower() in opportunity.location.lower():
        score += W_ELIGIBILITY
        reasons.append(MatchReason("Location", f"Available in {opportunity.location}.", W_ELIGIBILITY))

    # Deadline relevance: still open, and soon enough to act on.
    if opportunity.is_rolling:
        score += 5
        reasons.append(MatchReason("Timing", "Rolling applications — you can apply any time.", 5))
    elif opportunity.deadline:
        deadline = opportunity.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        days = (deadline - now).days
        if 0 <= days <= 30:
            score += W_DEADLINE
            when = (
                "Closes today"
                if days == 0
                else "Closes tomorrow"
                if days == 1
                else f"Closes in {days} days"
            )
            reasons.append(MatchReason("Timing", f"{when} — act soon.", W_DEADLINE))
        elif days > 30:
            score += 5
            reasons.append(MatchReason("Timing", "Still open with time to prepare.", 5))

    if opportunity.cost_type in (CostType.FREE.value, CostType.FREE_FOR_STUDENTS.value):
        score += W_COST
        reasons.append(MatchReason("Cost", "Free for students.", W_COST))

    reasons.sort(key=lambda r: r.points, reverse=True)
    return MatchResult(score=min(score, 100), reasons=reasons)
