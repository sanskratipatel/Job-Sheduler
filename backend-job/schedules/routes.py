from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import AsyncConnection

from database import get_db_connection

from .query import (
    archive_schedule,
    create_schedule,
    get_schedule_by_id,
    list_schedules,
    pause_schedule,
    resume_schedule,
    update_schedule,
)

from .requests import (
    CreateScheduleRequest,
    ScheduleConfig,
    UpdateScheduleRequest,
)

from .response import (
    ScheduleActionResponse,
    ScheduleListResponse,
    ScheduleResponse,
)

from schedules.service import (
    calculate_next_run_at,
    prepare_schedule_data,
)


router = APIRouter(
    prefix="/api/v1/schedules",
    tags=["Schedules"],
)


async def get_connection():
    async for connection in get_db_connection():
        yield connection


def _build_config_from_update(
    current: dict,
    update_data: dict,
) -> ScheduleConfig:
    """
    Merge the existing database schedule with PATCH fields,
    then validate the complete schedule configuration.
    """

    fields = {
        "name",
        "description",
        "job_type",
        "payload",
        "priority",
        "max_attempts",
        "timeout_seconds",
        "schedule_type",
        "timezone",
        "run_at",
        "run_time",
        "interval_count",
        "days_of_week",
        "day_of_month",
        "month_of_year",
        "run_dates",
        "cron_expression",
        "start_at",
        "end_at",
        "max_runs",
        "misfire_policy",
    }

    merged = {
        field: current.get(field)
        for field in fields
    }

    merged.update(update_data)

    return ScheduleConfig(**merged)


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule_api(
    request: CreateScheduleRequest,
    connection: AsyncConnection = Depends(get_connection),
):
    now = datetime.now(timezone.utc)

    try:
        data = prepare_schedule_data(
            request,
            now=now,
        )

        row = await create_schedule(
            connection,
            data=data,
        )

        if row is None:
            await connection.rollback()

            raise HTTPException(
                status_code=500,
                detail="Failed to create schedule",
            )

        await connection.commit()

        return row

    except HTTPException:
        raise

    except Exception as exc:
        await connection.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# LIST
# ============================================================

@router.get(
    "",
    response_model=ScheduleListResponse,
)
async def list_schedule_api(
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    schedule_type: str | None = None,
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
    items, total = await list_schedules(
        connection,
        status=status_filter,
        schedule_type=schedule_type,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# GET ONE
# ============================================================

@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
)
async def get_schedule_api(
    schedule_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    row = await get_schedule_by_id(
        connection,
        schedule_id=schedule_id,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    return row


# ============================================================
# UPDATE
# ============================================================

@router.patch(
    "/{schedule_id}",
    response_model=ScheduleResponse,
)
async def update_schedule_api(
    schedule_id: UUID,
    request: UpdateScheduleRequest,
    connection: AsyncConnection = Depends(get_connection),
):
    current = await get_schedule_by_id(
        connection,
        schedule_id=schedule_id,
    )

    if current is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    if current["status"] == "ARCHIVED":
        raise HTTPException(
            status_code=409,
            detail="Archived schedules cannot be updated",
        )

    update_data = request.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return current

    try:
        config = _build_config_from_update(
            current,
            update_data,
        )

        now = datetime.now(timezone.utc)

        prepared = prepare_schedule_data(
            config,
            now=now,
        )

        # Do not allow service-generated fields that
        # should not be changed through this PATCH.
        prepared.pop("next_run_at", None)

        # If timing/configuration changes, calculate
        # the next occurrence again.
        next_run_at = calculate_next_run_at(
            config,
            now=now,
        )

        if next_run_at is None:
            raise ValueError(
                "Updated schedule has no future execution time"
            )

        prepared["next_run_at"] = next_run_at

        row = await update_schedule(
            connection,
            schedule_id=schedule_id,
            data=prepared,
        )

        if row is None:
            await connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Schedule not found",
            )

        await connection.commit()

        return row

    except HTTPException:
        raise

    except Exception as exc:
        await connection.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# PAUSE
# ============================================================

@router.post(
    "/{schedule_id}/pause",
    response_model=ScheduleActionResponse,
)
async def pause_schedule_api(
    schedule_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    row = await pause_schedule(
        connection,
        schedule_id=schedule_id,
    )

    if row is None:
        current = await get_schedule_by_id(
            connection,
            schedule_id=schedule_id,
        )

        if current is None:
            raise HTTPException(
                status_code=404,
                detail="Schedule not found",
            )

        raise HTTPException(
            status_code=409,
            detail=(
                f"Schedule cannot be paused "
                f"because its current status is "
                f"{current['status']}"
            ),
        )

    await connection.commit()

    return {
        "id": row["id"],
        "status": row["status"],
        "message": "Schedule paused successfully",
    }


# ============================================================
# RESUME
# ============================================================

@router.post(
    "/{schedule_id}/resume",
    response_model=ScheduleActionResponse,
)
async def resume_schedule_api(
    schedule_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    current = await get_schedule_by_id(
        connection,
        schedule_id=schedule_id,
    )

    if current is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    if current["status"] != "PAUSED":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Only PAUSED schedules can be resumed. "
                f"Current status: {current['status']}"
            ),
        )

    try:
        config = ScheduleConfig(
            name=current["name"],
            description=current["description"],
            job_type=current["job_type"],
            payload=current["payload"],
            priority=current["priority"],
            max_attempts=current["max_attempts"],
            timeout_seconds=current["timeout_seconds"],
            schedule_type=current["schedule_type"],
            timezone=current["timezone"],
            run_at=current["run_at"],
            run_time=current["run_time"],
            interval_count=current["interval_count"],
            days_of_week=current["days_of_week"],
            day_of_month=current["day_of_month"],
            month_of_year=current["month_of_year"],
            run_dates=current["run_dates"],
            cron_expression=current["cron_expression"],
            start_at=current["start_at"],
            end_at=current["end_at"],
            max_runs=current["max_runs"],
            misfire_policy=current["misfire_policy"],
        )

        now = datetime.now(timezone.utc)

        next_run_at = calculate_next_run_at(
            config,
            now=now,
        )

        if next_run_at is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Schedule has no future execution time "
                    "and cannot be resumed"
                ),
            )

        row = await resume_schedule(
            connection,
            schedule_id=schedule_id,
            next_run_at=next_run_at,
        )

        if row is None:
            await connection.rollback()

            raise HTTPException(
                status_code=409,
                detail="Schedule could not be resumed",
            )

        await connection.commit()

        return {
            "id": row["id"],
            "status": row["status"],
            "message": "Schedule resumed successfully",
        }

    except HTTPException:
        raise

    except Exception as exc:
        await connection.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ============================================================
# ARCHIVE
# ============================================================

@router.delete(
    "/{schedule_id}",
    response_model=ScheduleActionResponse,
)
async def archive_schedule_api(
    schedule_id: UUID,
    connection: AsyncConnection = Depends(get_connection),
):
    row = await archive_schedule(
        connection,
        schedule_id=schedule_id,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found",
        )

    await connection.commit()

    return {
        "id": row["id"],
        "status": row["status"],
        "message": "Schedule archived successfully",
    }