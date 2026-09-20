from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ExecutionResponse(BaseModel):
    id: UUID
    job_id: UUID
    worker_id: UUID | None
    attempt_number: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    error_traceback: str | None
    output: dict[str, Any] | None
    created_at: datetime


class ExecutionListResponse(BaseModel):
    items: list[ExecutionResponse]
    total: int