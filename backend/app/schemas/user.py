from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Category, RemotePreference


class PreferencesIn(BaseModel):
    degree: str | None = Field(default=None, max_length=80)
    field_of_study: str | None = Field(default=None, max_length=120)
    year: str | None = Field(default=None, max_length=40)
    country: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=160)
    remote_preference: RemotePreference = RemotePreference.ANY
    skills: list[str] = []
    interests: list[str] = []
    preferred_categories: list[Category] = []


class PreferencesOut(PreferencesIn):
    model_config = ConfigDict(from_attributes=True)


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    is_admin: bool
    is_demo: bool = False
    preferences: PreferencesOut | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    preferences: PreferencesIn | None = None
