from pydantic import BaseModel, Field


class RegisterWorkerRequest(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    pid: int = Field(..., gt=0)
    concurrency: int = Field(default=1, ge=1)
    version: str | None = Field(default=None, max_length=100)
    git_sha: str | None = Field(default=None, max_length=100)