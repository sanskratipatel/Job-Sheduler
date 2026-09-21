from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator
from zoneinfo import ZoneInfo


ScheduleType = Literal[
    "ONCE",
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    "YEARLY",
    "SPECIFIC_DATES",
    "CRON",
]

MisfirePolicy = Literal[
    "SKIP",
    "RUN_ONCE",
]


class ScheduleConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

    job_type: str = Field(..., min_length=1, max_length=100)

    payload: dict[str, Any] = Field(default_factory=dict)

    priority: int = 0
    max_attempts: int = Field(default=3, ge=1, le=20)
    timeout_seconds: int = Field(default=300, gt=0)

    schedule_type: ScheduleType

    timezone: str = "UTC"

    run_at: datetime | None = None
    run_time: time | None = None

    interval_count: int = Field(default=1, ge=1)

    days_of_week: list[int] | None = None
    day_of_month: int | None = None
    month_of_year: int | None = None

    run_dates: list[date] | None = None

    cron_expression: str | None = Field(
        default=None,
        max_length=100,
    )

    start_at: datetime | None = None
    end_at: datetime | None = None

    max_runs: int | None = Field(
        default=None,
        gt=0,
    )

    misfire_policy: MisfirePolicy = "RUN_ONCE"

    @model_validator(mode="after")
    def validate_schedule(self):
        # --------------------------------------------------
        # Timezone
        # --------------------------------------------------
        try:
            ZoneInfo(self.timezone)
        except Exception as exc:
            raise ValueError(
                f"Invalid timezone: {self.timezone}"
            ) from exc

        # --------------------------------------------------
        # Datetime fields must be timezone-aware
        # --------------------------------------------------
        for field_name in ("run_at", "start_at", "end_at"):
            value = getattr(self, field_name)

            if value is not None and value.tzinfo is None:
                raise ValueError(
                    f"{field_name} must include timezone information"
                )

        # --------------------------------------------------
        # ONCE
        # --------------------------------------------------
        if self.schedule_type == "ONCE":
            if self.run_at is None:
                raise ValueError(
                    "run_at is required for ONCE schedules"
                )

        # --------------------------------------------------
        # CRON
        # --------------------------------------------------
        if self.schedule_type == "CRON":
            if not self.cron_expression:
                raise ValueError(
                    "cron_expression is required for CRON schedules"
                )

        # --------------------------------------------------
        # Calendar schedules
        # --------------------------------------------------
        calendar_types = {
            "DAILY",
            "WEEKLY",
            "MONTHLY",
            "YEARLY",
            "SPECIFIC_DATES",
        }

        if self.schedule_type in calendar_types:
            if self.run_time is None:
                raise ValueError(
                    "run_time is required for calendar schedules"
                )

        # --------------------------------------------------
        # WEEKLY
        # --------------------------------------------------
        if self.schedule_type == "WEEKLY":
            if not self.days_of_week:
                raise ValueError(
                    "days_of_week is required for WEEKLY schedules"
                )

            if any(
                day < 1 or day > 7
                for day in self.days_of_week
            ):
                raise ValueError(
                    "days_of_week values must be between 1 and 7"
                )

        # --------------------------------------------------
        # MONTHLY / YEARLY
        # --------------------------------------------------
        if self.schedule_type in {"MONTHLY", "YEARLY"}:
            if self.day_of_month is None:
                raise ValueError(
                    "day_of_month is required"
                )

            if not (
                1 <= self.day_of_month <= 31
                or self.day_of_month == -1
            ):
                raise ValueError(
                    "day_of_month must be between 1 and 31, "
                    "or -1 for the last day of the month"
                )

        # --------------------------------------------------
        # YEARLY
        # --------------------------------------------------
        if self.schedule_type == "YEARLY":
            if self.month_of_year is None:
                raise ValueError(
                    "month_of_year is required for YEARLY schedules"
                )

            if not 1 <= self.month_of_year <= 12:
                raise ValueError(
                    "month_of_year must be between 1 and 12"
                )

        # --------------------------------------------------
        # SPECIFIC_DATES
        # --------------------------------------------------
        if self.schedule_type == "SPECIFIC_DATES":
            if not self.run_dates:
                raise ValueError(
                    "run_dates is required for SPECIFIC_DATES schedules"
                )

        # --------------------------------------------------
        # end_at
        # --------------------------------------------------
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError(
                "end_at must be later than start_at"
            )

        return self


class CreateScheduleRequest(ScheduleConfig):
    pass


class UpdateScheduleRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    job_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    payload: dict[str, Any] | None = None

    priority: int | None = None

    max_attempts: int | None = Field(
        default=None,
        ge=1,
        le=20,
    )

    timeout_seconds: int | None = Field(
        default=None,
        gt=0,
    )

    schedule_type: ScheduleType | None = None

    timezone: str | None = None

    run_at: datetime | None = None
    run_time: time | None = None

    interval_count: int | None = Field(
        default=None,
        ge=1,
    )

    days_of_week: list[int] | None = None
    day_of_month: int | None = None
    month_of_year: int | None = None

    run_dates: list[date] | None = None

    cron_expression: str | None = Field(
        default=None,
        max_length=100,
    )

    start_at: datetime | None = None
    end_at: datetime | None = None

    max_runs: int | None = Field(
        default=None,
        gt=0,
    )

    misfire_policy: MisfirePolicy | None = None 

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field


class UpdateScheduleRequest(BaseModel):
    name: str | None = None
    description: str | None = None

    payload: dict[str, Any] | None = None

    priority: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    max_attempts: int | None = Field(
        default=None,
        ge=1,
    )

    timeout_seconds: int | None = Field(
        default=None,
        ge=1,
    )

    timezone: str | None = None

    run_at: datetime | None = None

    run_time: time | None = None

    interval_count: int | None = Field(
        default=None,
        ge=1,
    )

    days_of_week: list[int] | None = None

    day_of_month: int | None = Field(
        default=None,
        ge=1,
        le=31,
    )

    month_of_year: int | None = Field(
        default=None,
        ge=1,
        le=12,
    )

    run_dates: list[date] | None = None

    cron_expression: str | None = None

    start_at: datetime | None = None

    end_at: datetime | None = None

    max_runs: int | None = Field(
        default=None,
        ge=1,
    )

    misfire_policy: str | None = None