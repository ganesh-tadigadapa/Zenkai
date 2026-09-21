from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import create_all

logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description=(
        "Zenkai discovers opportunities scattered across the web — internships, "
        "hackathons, certifications, scholarships, programs and student benefits — "
        "and surfaces the ones relevant to a given student."
    ),
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    # Dev convenience. Production uses a migration tool (see DATABASE.md).
    if settings.ENV == "development":
        create_all()


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.ENV}
