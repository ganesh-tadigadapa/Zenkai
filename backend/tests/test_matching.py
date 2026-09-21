"""Recommendation scoring — the rules that drive 'Recommended for you'."""
from __future__ import annotations

from app.models.enums import Category, CostType, RemotePreference
from app.models.user import UserPreferences
from app.services.matching import W_CATEGORY, score_opportunity
from tests.conftest import make_opportunity


def prefs(**overrides) -> UserPreferences:
    base = dict(
        user_id="u1",
        remote_preference=RemotePreference.ANY.value,
        skills=["Python", "AWS"],
        interests=["Cloud", "AI"],
        preferred_categories=[Category.TECH_BENEFITS.value],
        location="Bengaluru, India",
    )
    base.update(overrides)
    return UserPreferences(**base)


def test_no_preferences_means_no_score(db):
    row = make_opportunity(db)
    assert score_opportunity(row, None).score == 0


def test_score_is_bounded_and_explained(db):
    row = make_opportunity(
        db,
        category=Category.TECH_BENEFITS,
        cost=CostType.FREE,
        skills=["Python", "AWS"],
        tags=["cloud", "ai"],
        deadline_days=10,
    )
    result = score_opportunity(row, prefs())
    assert 0 <= result.score <= 100
    assert result.score >= 80
    assert result.reasons
    assert sum(r.points for r in result.reasons) >= result.score - 1
    # Reasons are ordered by contribution so the UI can show the strongest first.
    assert [r.points for r in result.reasons] == sorted(
        (r.points for r in result.reasons), reverse=True
    )


def test_category_match_awards_its_weight(db):
    wanted = make_opportunity(db, title="Wanted", category=Category.TECH_BENEFITS,
                              skills=["Haskell"], tags=["obscure"], deadline_days=None)
    unwanted = make_opportunity(db, title="Unwanted", category=Category.SCHOLARSHIPS,
                                skills=["Haskell"], tags=["obscure"], deadline_days=None)
    p = prefs(interests=[], skills=[], remote_preference=RemotePreference.ONSITE.value,
              location="Nowhere")
    assert score_opportunity(wanted, p).score - score_opportunity(unwanted, p).score == W_CATEGORY


def test_interest_and_skill_overlap_increase_the_score(db):
    strong = make_opportunity(db, title="Strong", tags=["cloud", "ai"], skills=["Python", "AWS"])
    weak = make_opportunity(db, title="Weak", tags=["poetry"], skills=["Latin"])
    assert score_opportunity(strong, prefs()).score > score_opportunity(weak, prefs()).score


def test_reasons_name_the_matching_interest(db):
    row = make_opportunity(db, tags=["cloud"], skills=["Python"])
    reasons = score_opportunity(row, prefs()).reasons
    text = " ".join(r.detail.lower() for r in reasons)
    assert "cloud" in text
    assert any(r.label == "Skills" for r in reasons)


def test_imminent_deadlines_outrank_distant_ones(db):
    soon = make_opportunity(db, title="Soon", deadline_days=5)
    far = make_opportunity(db, title="Far", deadline_days=200)
    assert score_opportunity(soon, prefs()).score > score_opportunity(far, prefs()).score


def test_free_opportunities_score_above_paid_equivalents(db):
    free = make_opportunity(db, title="Free One", cost=CostType.FREE)
    paid = make_opportunity(db, title="Paid One", cost=CostType.PAID)
    assert score_opportunity(free, prefs()).score > score_opportunity(paid, prefs()).score


def test_remote_preference_is_respected(db):
    remote = make_opportunity(db, title="Remote", is_remote=True)
    onsite = make_opportunity(db, title="Onsite", is_remote=False, location="Berlin, Germany")
    p = prefs(remote_preference=RemotePreference.REMOTE.value, location="Bengaluru, India")
    assert score_opportunity(remote, p).score > score_opportunity(onsite, p).score


def test_location_match_counts_when_not_remote(db):
    local = make_opportunity(db, title="Local", is_remote=False, location="Bengaluru, India")
    far = make_opportunity(db, title="Far Away", is_remote=False, location="Berlin, Germany")
    p = prefs(remote_preference=RemotePreference.ONSITE.value)
    assert score_opportunity(local, p).score > score_opportunity(far, p).score


def test_relevance_sort_orders_the_feed_by_score(db, client, student):
    make_opportunity(db, title="Irrelevant", category=Category.SCHOLARSHIPS,
                     skills=["Latin"], tags=["poetry"], cost=CostType.PAID)
    make_opportunity(db, title="Relevant", category=Category.TECH_BENEFITS,
                     skills=["Python", "AWS"], tags=["cloud", "ai"], cost=CostType.FREE)

    items = client.get("/api/v1/opportunities?sort=relevance").json()["items"]
    assert [i["title"] for i in items] == ["Relevant", "Irrelevant"]
    assert items[0]["match"]["score"] > items[1]["match"]["score"]


def test_recommendations_endpoint_returns_scored_items(db, client, student):
    make_opportunity(db, title="Cloud Credits", category=Category.TECH_BENEFITS,
                     skills=["AWS"], tags=["cloud"])
    items = client.get("/api/v1/recommendations").json()
    assert items and items[0]["match"]["score"] > 0
    assert items[0]["match"]["reasons"]
