import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    "given",
    [
        "postgres://u:p@host:5432/db",
        "postgresql://u:p@host:5432/db",
        "postgresql+psycopg://u:p@host:5432/db",
    ],
)
def test_postgres_urls_use_the_psycopg_driver(given):
    assert Settings(DATABASE_URL=given).DATABASE_URL == "postgresql+psycopg://u:p@host:5432/db"


def test_sqlite_url_is_left_alone():
    assert Settings(DATABASE_URL="sqlite:///./x.db").DATABASE_URL == "sqlite:///./x.db"
