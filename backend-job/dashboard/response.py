from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    succeeded_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    active_workers: int
    active_schedules: int