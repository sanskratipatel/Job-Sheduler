from executions.query import list_executions_by_job
from executions.response import ExecutionListResponse
from uuid import UUID
from jobs.query import retry_job
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from psycopg import AsyncConnection

from database import get_db_connection
from jobs.query import (
    cancel_job,
    create_job,
    get_job_by_id,
    get_job_by_idempotency_key,
    get_job_type,
    list_jobs,
)
from jobs.request import CreateJobRequest
from jobs.response import (
    CancelJobResponse,
    JobListResponse,
    JobResponse,
)
from jobs.utils import generate_payload_hash


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


async def get_connection() -> AsyncConnection:
    async for connection in get_db_connection():
        return connection

    raise RuntimeError("Database connection could not be acquired")


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job_api(
    request: CreateJobRequest,
    connection: AsyncConnection = Depends(get_connection),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    payload_hash = generate_payload_hash(request.payload)

    # Validate job type
    job_type = await get_job_type(
        connection,
        request.job_type,
    )

    if job_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown job type: {request.job_type}",
        )

    if not job_type["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job type is inactive: {request.job_type}",
        )

    # Check idempotency
    if idempotency_key:
        existing_job = await get_job_by_idempotency_key(
            connection,
            idempotency_key,
        )

        if existing_job:

            if existing_job["payload_hash"] != payload_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Idempotency-Key was already used "
                        "with a different payload."
                    ),
                )

            return JobResponse(**existing_job)

    # Create job
    job = await create_job(
        connection,
        name=request.name,
        job_type=request.job_type,
        payload=request.payload,
        priority=request.priority,
        scheduled_at=request.scheduled_at,
        max_attempts=request.max_attempts,
        timeout_seconds=request.timeout_seconds,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )

    # Another concurrent request may have created the same idempotency key.
    if job is None and idempotency_key:

        existing_job = await get_job_by_idempotency_key(
            connection,
            idempotency_key,
        )

        if existing_job is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create job.",
            )

        if existing_job["payload_hash"] != payload_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Idempotency-Key was already used "
                    "with a different payload."
                ),
            )

        await connection.commit()

        return JobResponse(**existing_job)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job.",
        )

    await connection.commit()

    return JobResponse(**job)


@router.get(
    "",
    response_model=JobListResponse,
)
async def list_jobs_api(
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    job_type: str | None = Query(default=None),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    connection: AsyncConnection = Depends(get_connection),
):
    jobs, total = await list_jobs(
        connection,
        status=status_filter,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )

    return JobListResponse(
        items=[
            JobResponse(**job)
            for job in jobs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
async def get_job_api(
    job_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    job = await get_job_by_id(
        connection,
        job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return JobResponse(**job)


@router.post(
    "/{job_id}/cancel",
    response_model=CancelJobResponse,
)
async def cancel_job_api(
    job_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    job = await get_job_by_id(
        connection,
        job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    if job["status"] != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Job cannot be cancelled because "
                f"its current status is {job['status']}."
            ),
        )

    cancelled_job = await cancel_job(
        connection,
        job_id,
    )

    if cancelled_job is None:
        await connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job could not be cancelled.",
        )

    await connection.commit()

    return CancelJobResponse(
        id=cancelled_job["id"],
        status=cancelled_job["status"],
        message="Job cancelled successfully.",
    ) 

@router.get(
    "/{job_id}/executions",
    response_model=ExecutionListResponse,
)
async def list_job_executions_api(
    job_id: UUID,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    connection: AsyncConnection = Depends(get_connection),
):
    items, total = await list_executions_by_job(
        connection,
        job_id=job_id,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
 
     }  


@router.post(
    "/{job_id}/retry",
    response_model=CancelJobResponse,
)
async def retry_job_api(
    job_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    current = await get_job_by_id(
        connection,
        job_id=job_id,
    )

    if current is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if current["status"] != "FAILED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only FAILED jobs can be manually retried. "
                f"Current status: {current['status']}"
            ),
        )

    row = await retry_job(
        connection,
        job_id=job_id,
    )

    if row is None:
        await connection.rollback()

        raise HTTPException(
            status_code=409,
            detail="Job could not be retried",
        )

    await connection.commit()

    return {
        "id": row["id"],
        "status": row["status"],
        "message": "Job queued for retry",
    }