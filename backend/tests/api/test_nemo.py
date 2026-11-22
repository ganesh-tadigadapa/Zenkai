"""Nemo, the rule-based guide: what it understands and what it answers with."""
from __future__ import annotations

from app.models.enums import Category, CostType, OpportunityType
from app.services.nemo import understand
from tests.conftest import make_opportunity

CHAT = "/api/v1/nemo/chat"


# --- Understanding a message ----------------------------------------------------

def test_reads_category_topic_and_filters():
    u = understand("free remote Python internships closing this week")
    assert u.categories == [Category.INTERNSHIPS.value]
    assert [t.label for t in u.topics] == ["Python"]
    assert u.free_only is True
    assert u.remote is True
    assert u.within_days == 7


def test_short_words_match_whole_words_only():
    # "ai" is inside "email" and "java" is inside "javascript".
    assert understand("email me internships").topics == []
    assert [t.label for t in understand("javascript internships").topics] == ["JavaScript"]


def test_machine_learning_is_a_topic_not_a_request_for_courses():
    u = understand("machine learning internships")
    assert [t.label for t in u.topics] == ["machine learning"]
    assert u.categories == [Category.INTERNSHIPS.value]


def test_plain_chat_is_not_a_search():
    assert not understand("hello there").is_search
    assert not understand("thanks!").is_search


# --- The endpoint ---------------------------------------------------------------

def test_empty_message_returns_the_introduction(client):
    body = client.post(CHAT, json={"message": ""}).json()
    assert "Nemo" in body["reply"]
    assert body["opportunities"] == []
    assert body["suggestions"]


def test_search_returns_matching_opportunities_and_a_browse_link(db, client):
    make_opportunity(db, title="Python Backend Intern", category=Category.INTERNSHIPS,
                     opportunity_type=OpportunityType.INTERNSHIP)
    # The factory gives every record the skill "Python" unless told otherwise.
    make_opportunity(db, title="Design Intern", category=Category.INTERNSHIPS,
                     opportunity_type=OpportunityType.INTERNSHIP, skills=["Figma"])
    make_opportunity(db, title="Python Certification", category=Category.CERTIFICATIONS,
                     opportunity_type=OpportunityType.CERTIFICATION)

    body = client.post(CHAT, json={"message": "python internships"}).json()

    assert [o["title"] for o in body["opportunities"]] == ["Python Backend Intern"]
    assert body["browse_url"] == "/opportunities?category=internships&q=python"


def test_a_substring_hit_is_not_a_topic_match(db, client):
    # The database search for "ai" also finds "Maintenance"; Nemo must not.
    make_opportunity(db, title="Maintenance Engineering Intern", category=Category.INTERNSHIPS,
                     opportunity_type=OpportunityType.INTERNSHIP)
    make_opportunity(db, title="AI Research Intern", category=Category.INTERNSHIPS,
                     opportunity_type=OpportunityType.INTERNSHIP)

    body = client.post(CHAT, json={"message": "AI internships"}).json()

    assert [o["title"] for o in body["opportunities"]] == ["AI Research Intern"]


def test_free_only_excludes_paid(db, client):
    make_opportunity(db, title="Free Cloud Course", category=Category.CERTIFICATIONS,
                     opportunity_type=OpportunityType.COURSE, cost=CostType.FREE)
    make_opportunity(db, title="Paid Cloud Exam", category=Category.CERTIFICATIONS,
                     opportunity_type=OpportunityType.EXAM, cost=CostType.PAID)

    body = client.post(CHAT, json={"message": "free cloud certifications"}).json()

    assert [o["title"] for o in body["opportunities"]] == ["Free Cloud Course"]


def test_nothing_found_loosens_the_request_and_says_so(db, client):
    make_opportunity(db, title="Data Intern", category=Category.INTERNSHIPS,
                     opportunity_type=OpportunityType.INTERNSHIP)

    body = client.post(CHAT, json={"message": "rust internships"}).json()

    assert "couldn't find" in body["reply"]
    assert [o["title"] for o in body["opportunities"]] == ["Data Intern"]


def test_guidance_questions_get_an_answer(client):
    body = client.post(CHAT, json={"message": "how do I write a good resume?"}).json()
    assert "one page" in body["reply"]


def test_questions_about_the_site_do_not_turn_into_searches(db, client):
    make_opportunity(db, title="Free Thing")
    body = client.post(CHAT, json={"message": "is zenkai free?"}).json()
    assert body["opportunities"] == []
    assert "free" in body["reply"].lower()


def test_signed_in_results_carry_the_users_saved_state(db, client, student):
    opportunity = make_opportunity(db, title="Python Intern", category=Category.INTERNSHIPS,
                                   opportunity_type=OpportunityType.INTERNSHIP)
    client.post("/api/v1/saved", json={"opportunity_id": opportunity.id})

    body = client.post(CHAT, json={"message": "python internships"}).json()

    assert body["opportunities"][0]["is_saved"] is True


def test_overlong_messages_are_rejected(client):
    assert client.post(CHAT, json={"message": "x" * 501}).status_code == 422
