from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: UUID

    schedule_id: UUID | None

    scheduled_for: datetime | None

    name: str

    job_type: str

    status: str

    payload: dict[str, Any]

    priority: int

    scheduled_at: datetime

    attempt_count: int

    max_attempts: int

    timeout_seconds: int

    idempotency_key: str | None

    payload_hash: str | None

    locked_by: UUID | None

    locked_at: datetime | None

    lease_expires_at: datetime | None

    last_error: str | None

    started_at: datetime | None

    completed_at: datetime | None

    created_at: datetime

    updated_at: datetime


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    limit: int
    offset: int


class CancelJobResponse(BaseModel):
    id: UUID
    status: str
    message: str