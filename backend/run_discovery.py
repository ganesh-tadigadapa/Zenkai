"""Run discovery against registered sources. A real fetch, not a simulation.

    python run_discovery.py                      # every due, enabled source
    python run_discovery.py "Outreachy announcements"   # one named source
"""
from __future__ import annotations

import logging
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.scheduler import is_due
from app.models.source import Source

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)


def main(argv: list[str]) -> int:
    wanted = argv[1] if len(argv) > 1 else None
    pipeline = IngestionPipeline()

    with SessionLocal() as db:
        query = select(Source).where(Source.active.is_(True), Source.robots_allowed.is_(True))
        if wanted:
            query = query.where(Source.name == wanted)
        sources = list(db.scalars(query.order_by(Source.priority.desc())).all())

        if not sources:
            print(f"No enabled source matches {wanted!r}." if wanted else "No enabled sources.")
            return 1

        for source in sources:
            if not wanted and not is_due(source):
                print(f"- {source.name}: not due yet")
                continue

            print(f"\n=== {source.name} ({source.discovery_method}) ===")
            print(f"    {source.url}")
            report = pipeline.run_source(db, source)
            db.commit()

            print(f"    entries fetched  : {report.fetched}")
            print(f"    rejected as noise: {report.irrelevant}")
            print(f"    extracted        : {report.extracted}")
            print(f"    created          : {report.created}")
            print(f"    updated          : {report.updated}")
            print(f"    unchanged        : {report.unchanged}")
            print(f"    duplicates       : {report.duplicates}")
            if report.blocked_reason:
                print(f"    BLOCKED          : {report.blocked_reason}")
            for error in report.errors:
                print(f"    error            : {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
