from uuid import UUID
from jobs.response import JobListResponse
from workers.query import list_worker_jobs
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import AsyncConnection

from database import get_db_connection
from workers.query import (
    get_worker_by_id,
    heartbeat_worker,
    list_workers,
    register_worker,
    stop_worker,
)
from workers.request import RegisterWorkerRequest
from workers.response import (
    WorkerHeartbeatResponse,
    WorkerListResponse,
    WorkerResponse,
    WorkerStopResponse,
)


router = APIRouter(
    prefix="/api/v1/workers",
    tags=["Workers"],
)


async def get_connection():
    async for connection in get_db_connection():
        yield connection


@router.post(
    "/register",
    response_model=WorkerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_worker_api(
    request: RegisterWorkerRequest,
    connection: AsyncConnection = Depends(get_connection),
):
    worker = await register_worker(
        connection,
        hostname=request.hostname,
        pid=request.pid,
        concurrency=request.concurrency,
        version=request.version,
        git_sha=request.git_sha,
    )

    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register worker.",
        )

    await connection.commit()

    return WorkerResponse(**worker)


@router.get(
    "",
    response_model=WorkerListResponse,
)
async def list_workers_api(
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    connection: AsyncConnection = Depends(get_connection),
):
    workers, total = await list_workers(
        connection,
        status=status_filter,
    )

    return WorkerListResponse(
        items=[
            WorkerResponse(**worker)
            for worker in workers
        ],
        total=total,
    )


@router.get(
    "/{worker_id}",
    response_model=WorkerResponse,
)
async def get_worker_api(
    worker_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    worker = await get_worker_by_id(
        connection,
        worker_id,
    )

    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found.",
        )

    return WorkerResponse(**worker)


@router.post(
    "/{worker_id}/heartbeat",
    response_model=WorkerHeartbeatResponse,
)
async def heartbeat_worker_api(
    worker_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    worker = await heartbeat_worker(
        connection,
        worker_id,
    )

    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Worker does not exist or "
                "is not active."
            ),
        )

    await connection.commit()

    return WorkerHeartbeatResponse(
        id=worker["id"],
        status=worker["status"],
        last_heartbeat_at=worker["last_heartbeat_at"],
        message="Heartbeat recorded successfully.",
    )


@router.post(
    "/{worker_id}/stop",
    response_model=WorkerStopResponse,
)
async def stop_worker_api(
    worker_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    worker = await stop_worker(
        connection,
        worker_id,
    )

    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found or already stopped.",
        )

    await connection.commit()

    return WorkerStopResponse(
        id=worker["id"],
        status=worker["status"],
        stopped_at=worker["stopped_at"],
        message="Worker stopped successfully.",
    ) 

@router.get(
    "/{worker_id}/jobs",
    response_model=JobListResponse,
)
async def list_worker_jobs_api(
    worker_id: UUID,
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
    worker = await get_worker_by_id(
        connection,
        worker_id=worker_id,
    )

    if worker is None:
        raise HTTPException(
            status_code=404,
            detail="Worker not found",
        )

    items, total = await list_worker_jobs(
        connection,
        worker_id=worker_id,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }