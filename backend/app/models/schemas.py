from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobState(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PhotoFormat(StrEnum):
    SQUARE = "square"
    PORTRAIT = "portrait"
    DOUBLE_STRIP = "double_strip"


class Style(BaseModel):
    id: str
    name: str
    description: str
    preview_color: str
    prompt_template: str
    category: str = "travel"                 # "travel" | "culture"
    background_images: list[str] = []       # travel: person + background
    outfit_images: dict[str, list[str]] = {}  # culture: gender -> outfit files
    merch_image: str | None = None          # travel: optional style-specific merch file
    example_filter: str | None = None       # travel: sample "with filter" selfie
    example_nofilter: str | None = None     # travel: sample "without filter" selfie
    example: str | None = None              # culture: sample model photo in the costume (legacy)
    example_male: str | None = None         # culture: sample model photo in the male costume
    example_female: str | None = None       # culture: sample model photo in the female costume
    location_preview: str | None = None     # travel: 3:4 location preview for the style card


class CaptureResponse(BaseModel):
    image_id: UUID
    image_url: str


class GenerateRequest(BaseModel):
    image_ids: list[UUID] = Field(min_length=1, max_length=6)
    style_id: str
    photo_format: PhotoFormat


class PrintRequest(BaseModel):
    job_id: UUID


class JobResponse(BaseModel):
    job_id: UUID
    state: JobState
    message: str
    result_url: str | None = None
    attempt: int = 0


class ShareResponse(BaseModel):
    url: str


class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    state: JobState = JobState.QUEUED
    message: str = "Обработка фотографии... / Processing photo..."
    source_image_ids: list[UUID]
    style_id: str | None = None
    photo_format: PhotoFormat = PhotoFormat.PORTRAIT
    result_image_id: UUID | None = None
    attempt: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
