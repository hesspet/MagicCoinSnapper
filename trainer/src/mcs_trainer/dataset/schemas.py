from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


RAW_SCHEMA_VERSION = "mcs-raw-images-v1"
ANNOTATED_SCHEMA_VERSION = "mcs-annotated-dataset-v1"


class RawSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: Optional[str] = None
    contentType: Optional[str] = None
    sizeBytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    createdAt: Optional[datetime] = None
    notes: Optional[str] = None
    image: str
    tags: list[str] = Field(default_factory=list)


class RawMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str
    datasetId: str
    exportedAt: datetime
    source: Optional[str] = None
    samples: list[RawSample] = Field(default_factory=list)


class AnnotatedSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    image: str
    mask: str
    width: int
    height: int
    contentType: Optional[str] = None
    excluded: bool = False
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class AnnotatedMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str
    datasetId: str
    createdAt: datetime
    source: Optional[str] = None
    samples: list[AnnotatedSample] = Field(default_factory=list)
