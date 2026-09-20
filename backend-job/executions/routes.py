from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from database import get_db_connection
from executions.query import (
    get_execution_by_id,
    list_executions,
)
from executions.response import (
    ExecutionListResponse,
    ExecutionResponse,
)


router = APIRouter(
    prefix="/api/v1/executions",
    tags=["Executions"],
)


async def get_connection():
    async for connection in get_db_connection():
        yield connection


@router.get(
    "",
    response_model=ExecutionListResponse,
)
async def list_executions_api(
    job_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    connection: AsyncConnection = Depends(
        get_connection
    ),
):
    executions, total = await list_executions(
        connection,
        job_id=job_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return ExecutionListResponse(
        items=[
            ExecutionResponse(**execution)
            for execution in executions
        ],
        total=total,
    )


@router.get(
    "/{execution_id}",
    response_model=ExecutionResponse,
)
async def get_execution_api(
    execution_id: UUID,
    connection: AsyncConnection = Depends(
        get_connection
    ),
):
    execution = await get_execution_by_id(
        connection,
        execution_id,
    )

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail="Execution not found.",
        )

    return ExecutionResponse(**execution)