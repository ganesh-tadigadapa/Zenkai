"""Creation, retrieval, filtering, search and deadline sorting."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.enums import Category, CostType, OpportunityType, VerificationStatus
from app.repositories.opportunity_repository import OpportunityQuery
from app.services import opportunity_service as svc
from tests.conftest import make_opportunity, make_org


def test_create_opportunity_generates_unique_slugs(db):
    make_opportunity(db, title="Cloud Program")
    org = make_org(db, "Second Org")
    assert svc.unique_slug(db, "Cloud Program") == "cloud-program-2"
    assert svc.slugify("AWS  Cloud — Student Program!") == "aws-cloud-student-program"
    assert org is not None


def test_retrieval_by_id_and_slug(db, client):
    row = make_opportunity(db, title="Findable Thing")
    by_id = client.get(f"/api/v1/opportunities/{row.id}")
    by_slug = client.get("/api/v1/opportunities/findable-thing")
    assert by_id.status_code == 200
    assert by_slug.status_code == 200
    assert by_id.json()["id"] == by_slug.json()["id"] == row.id
    assert by_id.json()["description"]  # detail payload carries the full body


def test_missing_opportunity_returns_404(client):
    assert client.get("/api/v1/opportunities/does-not-exist").status_code == 404


def test_rejected_opportunities_are_hidden_from_the_public_api(db, client):
    row = make_opportunity(db, title="Bad Record", status=VerificationStatus.REJECTED)
    assert client.get(f"/api/v1/opportunities/{row.id}").status_code == 404
    titles = [i["title"] for i in client.get("/api/v1/opportunities").json()["items"]]
    assert "Bad Record" not in titles


def test_expired_opportunities_excluded_unless_requested(db, client):
    make_opportunity(db, title="Long Gone", deadline_days=-5)
    make_opportunity(db, title="Still Open", deadline_days=5)

    default = [i["title"] for i in client.get("/api/v1/opportunities").json()["items"]]
    assert default == ["Still Open"]

    with_expired = [
        i["title"]
        for i in client.get("/api/v1/opportunities?include_expired=true").json()["items"]
    ]
    assert set(with_expired) == {"Long Gone", "Still Open"}


def test_filter_by_category_type_and_cost(db, client):
    make_opportunity(db, title="Free Cloud Tool", category=Category.TECH_BENEFITS, cost=CostType.FREE)
    make_opportunity(
        db,
        title="Paid Exam",
        category=Category.CERTIFICATIONS,
        opportunity_type=OpportunityType.CERTIFICATION,
        cost=CostType.PAID,
    )

    only_benefits = client.get("/api/v1/opportunities?category=tech_benefits").json()
    assert only_benefits["total"] == 1
    assert only_benefits["items"][0]["title"] == "Free Cloud Tool"

    assert client.get("/api/v1/opportunities?type=certification").json()["total"] == 1
    assert client.get("/api/v1/opportunities?free_only=true").json()["total"] == 1
    assert client.get("/api/v1/opportunities?cost=paid").json()["total"] == 1


def test_filter_by_remote_and_location(db, client):
    make_opportunity(db, title="Remote Role", is_remote=True, location="Global")
    make_opportunity(db, title="Onsite Role", is_remote=False, location="Bengaluru, India")

    assert client.get("/api/v1/opportunities?remote=true").json()["total"] == 1
    assert client.get("/api/v1/opportunities?remote=false").json()["total"] == 1
    located = client.get("/api/v1/opportunities?location=bengaluru").json()
    assert located["total"] == 1 and located["items"][0]["title"] == "Onsite Role"


def test_verified_only_filter(db, client):
    make_opportunity(db, title="Checked", status=VerificationStatus.CURATED)
    make_opportunity(db, title="Unchecked", status=VerificationStatus.NEEDS_REVIEW)

    assert client.get("/api/v1/opportunities").json()["total"] == 2
    verified = client.get("/api/v1/opportunities?verified_only=true").json()
    assert verified["total"] == 1 and verified["items"][0]["title"] == "Checked"


def test_search_spans_title_organization_description_skills_and_tags(db, client):
    org = make_org(db, "Kubernetes Foundation")
    make_opportunity(db, title="Alpha Grant", org=org)
    make_opportunity(db, title="Beta Fellowship", skills=["Rust"], tags=["systems"])

    def titles(query: str):
        return {i["title"] for i in client.get(f"/api/v1/opportunities?q={query}").json()["items"]}

    assert titles("alpha") == {"Alpha Grant"}                 # title
    assert titles("kubernetes") == {"Alpha Grant"}            # organisation name
    assert titles("rust") == {"Beta Fellowship"}              # skills JSON
    assert titles("systems") == {"Beta Fellowship"}           # tags JSON
    assert titles("description") == {"Alpha Grant", "Beta Fellowship"}  # description
    assert titles("nothingmatchesthis") == set()


def test_search_is_case_insensitive(db, client):
    make_opportunity(db, title="MongoDB Atlas")
    assert client.get("/api/v1/opportunities?q=mongodb").json()["total"] == 1
    assert client.get("/api/v1/opportunities?q=MONGODB").json()["total"] == 1


def test_deadline_sorting_puts_soonest_first_and_undated_last(db, client):
    make_opportunity(db, title="Later", deadline_days=30)
    make_opportunity(db, title="Sooner", deadline_days=2)
    make_opportunity(db, title="Undated", deadline_days=None)

    order = [i["title"] for i in client.get("/api/v1/opportunities?sort=deadline").json()["items"]]
    assert order == ["Sooner", "Later", "Undated"]


def test_deadline_within_days_filter(db, client):
    make_opportunity(db, title="This Week", deadline_days=3)
    make_opportunity(db, title="Next Month", deadline_days=40)

    soon = client.get("/api/v1/opportunities?deadline_within_days=7").json()
    assert soon["total"] == 1 and soon["items"][0]["title"] == "This Week"


def test_days_left_is_computed_for_dated_records_only(db):
    dated = make_opportunity(db, title="Dated", deadline_days=9)
    rolling = make_opportunity(db, title="Rolling", deadline_days=None, is_rolling=True)
    assert svc.days_left(dated) == 9
    assert svc.days_left(rolling) is None


def test_pagination_reports_total_independently_of_limit(db, client):
    for n in range(5):
        make_opportunity(db, title=f"Item {n}", deadline_days=n + 1)

    page = client.get("/api/v1/opportunities?limit=2&offset=2").json()
    assert page["total"] == 5
    assert len(page["items"]) == 2
    assert page["items"][0]["title"] == "Item 2"


def test_expire_passed_deadlines_updates_status(db):
    stale = make_opportunity(db, title="Stale", deadline_days=-1)
    fresh = make_opportunity(db, title="Fresh", deadline_days=5)
    assert svc.expire_passed_deadlines(db) == 1
    assert stale.verification_status == VerificationStatus.EXPIRED.value
    assert fresh.verification_status == VerificationStatus.CURATED.value


def test_facets_count_public_records(db, client):
    make_opportunity(db, title="A", category=Category.TECH_BENEFITS)
    make_opportunity(db, title="B", category=Category.TECH_BENEFITS)
    make_opportunity(db, title="C", category=Category.SCHOLARSHIPS)

    facets = client.get("/api/v1/opportunities/facets").json()
    by_value = {f["value"]: f["count"] for f in facets["category"]}
    assert by_value["tech_benefits"] == 2
    assert by_value["scholarships"] == 1


def test_categories_endpoint_always_returns_all_six(db, client):
    make_opportunity(db, title="Only One", category=Category.HACKATHONS)
    categories = client.get("/api/v1/categories").json()
    assert len(categories) == 6
    counts = {c["slug"]: c["count"] for c in categories}
    assert counts["hackathons"] == 1
    assert counts["scholarships"] == 0


def test_query_object_defaults_are_safe(db):
    rows, total = svc.list_opportunities(db, OpportunityQuery(), None)
    assert rows == [] and total == 0
