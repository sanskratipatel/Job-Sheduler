from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WorkerResponse(BaseModel):
    id: UUID
    hostname: str
    pid: int
    status: str
    concurrency: int
    version: str | None
    git_sha: str | None
    started_at: datetime
    last_heartbeat_at: datetime
    stopped_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkerListResponse(BaseModel):
    items: list[WorkerResponse]
    total: int


class WorkerHeartbeatResponse(BaseModel):
    id: UUID
    status: str
    last_heartbeat_at: datetime
    message: str


class WorkerStopResponse(BaseModel):
    id: UUID
    status: str
    stopped_at: datetime
    message: str