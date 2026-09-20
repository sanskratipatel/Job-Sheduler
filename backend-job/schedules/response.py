from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ScheduleResponse(BaseModel):
    id: UUID

    name: str
    description: str | None

    job_type: str

    payload: dict[str, Any]

    priority: int
    max_attempts: int
    timeout_seconds: int

    schedule_type: str
    timezone: str

    run_at: datetime | None
    run_time: time | None

    interval_count: int

    days_of_week: list[int] | None
    day_of_month: int | None
    month_of_year: int | None

    run_dates: list[date] | None

    cron_expression: str | None

    start_at: datetime
    end_at: datetime | None

    max_runs: int | None

    misfire_policy: str

    status: str

    next_run_at: datetime | None
    last_run_at: datetime | None

    run_count: int

    created_at: datetime
    updated_at: datetime


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int
    limit: int
    offset: int


class ScheduleActionResponse(BaseModel):
    id: UUID
    status: str
    message: str