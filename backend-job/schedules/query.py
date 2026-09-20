from typing import Any
from uuid import UUID

from psycopg import AsyncConnection


SCHEDULE_COLUMNS = """
    id,
    name,
    description,
    job_type,
    payload,
    priority,
    max_attempts,
    timeout_seconds,
    schedule_type,
    timezone,
    run_at,
    run_time,
    interval_count,
    days_of_week,
    day_of_month,
    month_of_year,
    run_dates,
    cron_expression,
    start_at,
    end_at,
    max_runs,
    misfire_policy,
    status,
    next_run_at,
    last_run_at,
    run_count,
    created_at,
    updated_at
"""


async def create_schedule(
    connection: AsyncConnection,
    *,
    data: dict[str, Any],
):
    query = f"""
        INSERT INTO job_schedules (
            name,
            description,
            job_type,
            payload,
            priority,
            max_attempts,
            timeout_seconds,
            schedule_type,
            timezone,
            run_at,
            run_time,
            interval_count,
            days_of_week,
            day_of_month,
            month_of_year,
            run_dates,
            cron_expression,
            start_at,
            end_at,
            max_runs,
            misfire_policy,
            status,
            next_run_at
        )
        VALUES (
            %(name)s,
            %(description)s,
            %(job_type)s,
            %(payload)s,
            %(priority)s,
            %(max_attempts)s,
            %(timeout_seconds)s,
            %(schedule_type)s,
            %(timezone)s,
            %(run_at)s,
            %(run_time)s,
            %(interval_count)s,
            %(days_of_week)s,
            %(day_of_month)s,
            %(month_of_year)s,
            %(run_dates)s,
            %(cron_expression)s,
            %(start_at)s,
            %(end_at)s,
            %(max_runs)s,
            %(misfire_policy)s,
            'ACTIVE',
            %(next_run_at)s
        )
        RETURNING {SCHEDULE_COLUMNS};
    """

    async with connection.cursor() as cursor:
        await cursor.execute(query, data)

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def get_schedule_by_id(
    connection: AsyncConnection,
    *,
    schedule_id: UUID,
):
    query = f"""
        SELECT {SCHEDULE_COLUMNS}
        FROM job_schedules
        WHERE id = %(schedule_id)s;
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "schedule_id": schedule_id,
            },
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def list_schedules(
    connection: AsyncConnection,
    *,
    status: str | None = None,
    schedule_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    conditions = []
    params: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }

    if status is not None:
        conditions.append(
            "status = %(status)s"
        )
        params["status"] = status

    if schedule_type is not None:
        conditions.append(
            "schedule_type = %(schedule_type)s"
        )
        params["schedule_type"] = schedule_type

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE " + " AND ".join(conditions)
        )

    count_query = f"""
        SELECT COUNT(*) AS total
        FROM job_schedules
        {where_clause};
    """

    list_query = f"""
        SELECT {SCHEDULE_COLUMNS}
        FROM job_schedules
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT %(limit)s
        OFFSET %(offset)s;
    """

    async with connection.cursor() as cursor:

        # -------------------------------
        # Total count
        # -------------------------------
        await cursor.execute(
            count_query,
            params,
        )

        count_row = await cursor.fetchone()

        total = count_row[0] if count_row else 0

        # -------------------------------
        # Schedule rows
        # -------------------------------
        await cursor.execute(
            list_query,
            params,
        )

        rows = await cursor.fetchall()

        columns = [
            column.name
            for column in cursor.description
        ]

        items = [
            dict(zip(columns, row))
            for row in rows
        ]

    return items, total


async def update_schedule(
    connection: AsyncConnection,
    *,
    schedule_id: UUID,
    data: dict[str, Any],
):
    if not data:
        return await get_schedule_by_id(
            connection,
            schedule_id=schedule_id,
        )

    allowed_fields = {
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
        "next_run_at",
    }

    invalid_fields = set(data) - allowed_fields

    if invalid_fields:
        raise ValueError(
            f"Invalid schedule fields: {invalid_fields}"
        )

    set_clauses = []

    params: dict[str, Any] = {
        "schedule_id": schedule_id,
    }

    for field, value in data.items():
        set_clauses.append(
            f"{field} = %({field})s"
        )
        params[field] = value

    query = f"""
        UPDATE job_schedules
        SET
            {", ".join(set_clauses)}
        WHERE id = %(schedule_id)s
        RETURNING {SCHEDULE_COLUMNS};
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            params,
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def pause_schedule(
    connection: AsyncConnection,
    *,
    schedule_id: UUID,
):
    query = f"""
        UPDATE job_schedules
        SET
            status = 'PAUSED'
        WHERE id = %(schedule_id)s
          AND status = 'ACTIVE'
        RETURNING {SCHEDULE_COLUMNS};
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "schedule_id": schedule_id,
            },
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def resume_schedule(
    connection: AsyncConnection,
    *,
    schedule_id: UUID,
    next_run_at,
):
    query = f"""
        UPDATE job_schedules
        SET
            status = 'ACTIVE',
            next_run_at = %(next_run_at)s
        WHERE id = %(schedule_id)s
          AND status = 'PAUSED'
        RETURNING {SCHEDULE_COLUMNS};
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "schedule_id": schedule_id,
                "next_run_at": next_run_at,
            },
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def archive_schedule(
    connection: AsyncConnection,
    *,
    schedule_id: UUID,
):
    query = f"""
        UPDATE job_schedules
        SET
            status = 'ARCHIVED',
            next_run_at = NULL
        WHERE id = %(schedule_id)s
          AND status <> 'ARCHIVED'
        RETURNING {SCHEDULE_COLUMNS};
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "schedule_id": schedule_id,
            },
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))