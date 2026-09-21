"""Is this feed item a student opportunity at all?

Most of what a real feed carries is not. AWS's announcement feed is a hundred
product releases; a jobs feed is mostly senior roles. Without this stage, going
live means filling the catalogue with things no student can apply to — which is
worse than an empty catalogue, because it teaches people not to trust it.

The gate is deliberately conservative: an item is rejected unless there is
positive evidence it describes an opportunity in one of Zenkai's six
categories. Rejecting something real costs one missed record that a human can
add. Accepting something irrelevant costs the catalogue's credibility.

Every decision carries a reason, so the review queue can be audited rather than
taken on faith.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.enums import Category

#: Phrases that indicate an opportunity someone can take up. Weighted: a
#: deadline or an open application is much stronger evidence than a bare
#: mention of "program".
STRONG_SIGNALS: dict[str, tuple[str, Category]] = {
    r"\bapplications? (?:are )?(?:now )?open\b": ("applications are open", Category.PROGRAMS),
    r"\bapply (?:now|today|here|by)\b": ("invites applications", Category.PROGRAMS),
    r"\bcall for (?:applications|participants|mentors|proposals)\b": (
        "call for applications",
        Category.PROGRAMS,
    ),
    r"\binternships?\b": ("mentions internships", Category.INTERNSHIPS),
    r"\bscholarships?\b": ("mentions scholarships", Category.SCHOLARSHIPS),
    r"\bfellowships?\b": ("mentions fellowships", Category.PROGRAMS),
    r"\bhackathons?\b": ("mentions a hackathon", Category.HACKATHONS),
    r"\bfree for students\b": ("free for students", Category.TECH_BENEFITS),
    r"\bstudent (?:pack|program(?:me)?|plan|offer|discount|benefit)\b": (
        "a student programme or benefit",
        Category.TECH_BENEFITS,
    ),
    r"\b(?:certification|credential) (?:program(?:me)?|exam|path)\b": (
        "a certification programme",
        Category.CERTIFICATIONS,
    ),
    # "grants" is a verb far more often than a noun in technology writing
    # ("grants permission", "grants access"), so it only counts when it reads
    # like funding.
    r"\b(?:research|travel|student|study|education|funding)\s+grants?\b"
    r"|\bgrants?\s+(?:program(?:me)?|scheme|fund|application)\b": (
        "mentions a funding grant",
        Category.SCHOLARSHIPS,
    ),
    r"\bmentorship (?:program(?:me)?|round|cohort)\b": (
        "a mentorship programme",
        Category.PROGRAMS,
    ),
    r"\bstipend\b": ("mentions a stipend", Category.PROGRAMS),
}

#: Bare nouns that are strong evidence as a *subject* and weak evidence in
#: passing. "AWS Training and Certification" appearing inside a product
#: announcement does not make that announcement a certification, so these only
#: count when they are in the title.
TITLE_ONLY_SIGNALS: dict[str, tuple[str, Category]] = {
    r"\bcertifications?\b|\bcertified\b": ("a certification", Category.CERTIFICATIONS),
    r"\bcohort\b": ("a cohort programme", Category.PROGRAMS),
    r"\b(?:digital|professional|micro)[ -]credential\b": (
        "a named credential",
        Category.CERTIFICATIONS,
    ),
}

#: Supporting evidence. Not enough alone, but reinforces a strong signal.
SUPPORTING_SIGNALS: tuple[tuple[str, str], ...] = (
    (r"\bdeadline\b", "states a deadline"),
    (r"\beligib(?:le|ility)\b", "states eligibility"),
    (r"\bhow to apply\b", "explains how to apply"),
    (r"\bopen to (?:students|applicants|everyone)\b", "states who may apply"),
    (r"\benrol(?:l)?(?:ment)?\b", "mentions enrolment"),
    (r"\bno cost\b|\bat no charge\b", "states it is free"),
)

#: Product-release language. Its presence does not veto an item on its own, but
#: an item carrying only this and no strong signal is an announcement, not an
#: opportunity.
PRODUCT_ANNOUNCEMENT: tuple[str, ...] = (
    r"\bnow (?:supports?|available|offers?|generally available)\b",
    r"\bis now (?:ga|generally available)\b",
    r"\bannouncing (?:support|the availability|general availability)\b",
    r"\badds? (?:support|new capabilit)",
    r"\bnew (?:feature|version|release|region)s?\b",
    r"\bexpands? to\b",
    r"\bextends? support\b",
    r"\bat no additional cost\b",
    r"\bprice (?:reduction|change)\b",
)

#: How much evidence is needed to let an item through to extraction.
ACCEPT_THRESHOLD = 2


@dataclass
class RelevanceVerdict:
    """Why an item was accepted or rejected, in words a reviewer can check."""

    relevant: bool
    score: int
    reasons: list[str] = field(default_factory=list)
    category: Category | None = None
    #: Present on rejection.
    rejected_because: str | None = None


def _matches(patterns, text: str):
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            yield pattern


def assess(
    title: str, summary: str = "", catalogue: str | None = None
) -> RelevanceVerdict:
    """Decide whether an item is worth extracting as an opportunity.

    Scoring: each strong signal is worth 2, each supporting signal 1. An item
    needs ACCEPT_THRESHOLD to pass, so one strong signal alone is enough, as is
    two supporting ones alongside nothing contradictory.
    """
    # A typed catalogue endpoint has already answered this question. When an
    # adapter reads `?type=certifications`, every record it returns is a
    # certification by construction, and a text heuristic cannot improve on
    # that — it can only get it wrong. This is an adapter asserting a known
    # fact about its source, not a way around the gate: only adapters set it,
    # and a feed can never claim it.
    if catalogue:
        try:
            known = Category(catalogue)
        except ValueError:
            known = None
        if known is not None:
            return RelevanceVerdict(
                True, 99, [f"from a {catalogue} catalogue endpoint"], category=known
            )

    text = f"{title} {summary}".strip()
    if not text:
        return RelevanceVerdict(False, 0, rejected_because="no text to assess")

    score = 0
    reasons: list[str] = []
    category: Category | None = None
    #: Whether an unambiguous signal fired, as opposed to only a bare noun.
    unambiguous = False

    for pattern, (reason, mapped) in STRONG_SIGNALS.items():
        if re.search(pattern, text, re.IGNORECASE):
            score += 2
            reasons.append(reason)
            unambiguous = True
            if category is None:
                category = mapped

    # Bare nouns count only as the subject of the item, not in passing.
    for pattern, (reason, mapped) in TITLE_ONLY_SIGNALS.items():
        if re.search(pattern, title, re.IGNORECASE):
            score += 2
            reasons.append(f"{reason} in the title")
            if category is None:
                category = mapped

    for pattern, reason in SUPPORTING_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 1
            reasons.append(reason)

    announcement_hits = list(_matches(PRODUCT_ANNOUNCEMENT, text))

    # Release-note language in the *title* settles it. "X now supports Y" is an
    # announcement whatever nouns appear beside it, and a bare noun is too weak
    # to overturn that — "now supports credential testing" is about passwords,
    # not qualifications. An unambiguous signal ("applications are open") still
    # wins, because a programme announcement can legitimately be phrased that
    # way.
    if not unambiguous and list(_matches(PRODUCT_ANNOUNCEMENT, title)):
        return RelevanceVerdict(
            False,
            score,
            reasons,
            rejected_because="the title reads as a product announcement",
        )

    # Product-release language with no strong signal is an announcement. This
    # is the case that keeps a vendor's release feed out of the catalogue.
    if announcement_hits and category is None:
        return RelevanceVerdict(
            False,
            score,
            reasons,
            rejected_because="reads as a product announcement, not an opportunity",
        )

    # Supporting signals reinforce; they never establish on their own. A page
    # can state eligibility and a price without being an opportunity — that
    # describes most product documentation. At least one strong signal is
    # required before anything is accepted.
    if category is None:
        return RelevanceVerdict(
            False,
            score,
            reasons,
            rejected_because="no signal that this is an opportunity a student can take up",
        )

    if score < ACCEPT_THRESHOLD:
        return RelevanceVerdict(
            False,
            score,
            reasons,
            rejected_because="too little evidence to treat this as an opportunity",
        )

    return RelevanceVerdict(True, score, reasons, category=category)
