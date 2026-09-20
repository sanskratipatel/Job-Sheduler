from typing import Any
from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name of the job",
    )
    job_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Job type code, for example SEND_EMAIL",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Data required by the job handler",
    )
    priority: int = Field(
        default=0,
        description="Higher priority jobs are claimed first",
    )
    scheduled_at: Any = Field(
        default=None,
        description="Time after which the worker can claim the job",
    )
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of execution attempts",
    )
    timeout_seconds: int = Field(
        default=300,
        gt=0,
        description="Maximum allowed execution time",
    )