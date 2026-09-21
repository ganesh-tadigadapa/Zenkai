from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


class FacetValue(BaseModel):
    value: str
    label: str
    count: int


class Message(BaseModel):
    detail: str


class StatsOut(BaseModel):
    total: int = Field(description="Verified, non-expired opportunities")
    new_today: int
    closing_soon: int
    saved: int
    matched: int
