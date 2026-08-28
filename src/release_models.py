"""Typed inputs and observable release records."""

from enum import StrEnum

from pydantic import BaseModel, Field


class BuildState(StrEnum):
    QUEUED = "queued"
    GENERATED = "generated"
    RELEASED = "released"


class DeveloperImageRequest(BaseModel):
    build_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{2,63}$")
    release_tag: str = Field(min_length=1, max_length=80)
    prompt: str = Field(min_length=10, max_length=2000)
    size: str = Field(default="1024x1024", pattern=r"^(1024x1024|1024x1792|1792x1024)$")


class BuildEvent(BaseModel):
    state: BuildState
    detail: str


class ImageRelease(BaseModel):
    build_id: str
    release_tag: str
    artifact_path: str
    byte_count: int
    events: list[BuildEvent]
    diagnostics: list[str]
