from datetime import datetime
from typing import Any

from psycopg import AsyncConnection
from psycopg.types.json import Jsonb


CREATE_JOB_QUERY = """
INSERT INTO jobs (
    name,
    job_type,
    payload,
    priority,
    scheduled_at,
    max_attempts,
    timeout_seconds
)
VALUES (
    %(name)s,
    %(job_type)s,
    %(payload)s,
    %(priority)s,
    COALESCE(%(scheduled_at)s, NOW()),
    %(max_attempts)s,
    %(timeout_seconds)s
)
RETURNING
    id,
    schedule_id,
    scheduled_for,
    name,
    job_type,
    status,
    payload,
    priority,
    scheduled_at,
    attempt_count,
    max_attempts,
    timeout_seconds,
    idempotency_key,
    payload_hash,
    locked_by,
    locked_at,
    lease_expires_at,
    last_error,
    started_at,
    completed_at,
    created_at,
    updated_at;
"""


async def create_job(
    connection: AsyncConnection,
    *,
    name: str,
    job_type: str,
    payload: dict[str, Any],
    priority: int,
    scheduled_at: datetime | None,
    max_attempts: int,
    timeout_seconds: int,
) -> dict | None:

    params = {
        "name": name,
        "job_type": job_type,
        "payload": Jsonb(payload),
        "priority": priority,
        "scheduled_at": scheduled_at,
        "max_attempts": max_attempts,
        "timeout_seconds": timeout_seconds,
    }

    async with connection.cursor() as cursor:
        await cursor.execute(
            CREATE_JOB_QUERY,
            params,
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row)) 

from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.types.json import Jsonb


JOB_COLUMNS = """
    id,
    schedule_id,
    scheduled_for,
    name,
    job_type,
    status,
    payload,
    priority,
    scheduled_at,
    attempt_count,
    max_attempts,
    timeout_seconds,
    idempotency_key,
    payload_hash,
    locked_by,
    locked_at,
    lease_expires_at,
    last_error,
    started_at,
    completed_at,
    created_at,
    updated_at
"""


async def get_job_type(
    connection: AsyncConnection,
    job_type: str,
) -> dict | None:

    query = """
        SELECT code, name, description, is_active
        FROM job_types
        WHERE code = %(job_type)s
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"job_type": job_type},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def create_job(
    connection: AsyncConnection,
    *,
    name: str,
    job_type: str,
    payload: dict[str, Any],
    priority: int,
    scheduled_at: datetime | None,
    max_attempts: int,
    timeout_seconds: int,
    idempotency_key: str | None,
    payload_hash: str,
) -> dict | None:

    query = f"""
        INSERT INTO jobs (
            name,
            job_type,
            payload,
            priority,
            scheduled_at,
            max_attempts,
            timeout_seconds,
            idempotency_key,
            payload_hash
        )
        VALUES (
            %(name)s,
            %(job_type)s,
            %(payload)s,
            %(priority)s,
            COALESCE(%(scheduled_at)s, NOW()),
            %(max_attempts)s,
            %(timeout_seconds)s,
            %(idempotency_key)s,
            %(payload_hash)s
        )
        ON CONFLICT DO NOTHING
        RETURNING {JOB_COLUMNS}
    """

    params = {
        "name": name,
        "job_type": job_type,
        "payload": Jsonb(payload),
        "priority": priority,
        "scheduled_at": scheduled_at,
        "max_attempts": max_attempts,
        "timeout_seconds": timeout_seconds,
        "idempotency_key": idempotency_key,
        "payload_hash": payload_hash,
    }

    async with connection.cursor() as cursor:
        await cursor.execute(query, params)

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def get_job_by_id(
    connection: AsyncConnection,
    job_id: UUID,
) -> dict | None:

    query = f"""
        SELECT {JOB_COLUMNS}
        FROM jobs
        WHERE id = %(job_id)s
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"job_id": job_id},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def get_job_by_idempotency_key(
    connection: AsyncConnection,
    idempotency_key: str,
) -> dict | None:

    query = f"""
        SELECT {JOB_COLUMNS}
        FROM jobs
        WHERE idempotency_key = %(idempotency_key)s
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"idempotency_key": idempotency_key},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def list_jobs(
    connection: AsyncConnection,
    *,
    status: str | None,
    job_type: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:

    where_conditions = []
    params = {
        "limit": limit,
        "offset": offset,
    }

    if status:
        where_conditions.append("status = %(status)s")
        params["status"] = status

    if job_type:
        where_conditions.append("job_type = %(job_type)s")
        params["job_type"] = job_type

    where_clause = ""

    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    count_query = f"""
        SELECT COUNT(*)
        FROM jobs
        {where_clause}
    """

    data_query = f"""
        SELECT {JOB_COLUMNS}
        FROM jobs
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT %(limit)s
        OFFSET %(offset)s
    """

    async with connection.cursor() as cursor:

        await cursor.execute(count_query, params)

        count_row = await cursor.fetchone()
        total = count_row[0]

        await cursor.execute(data_query, params)

        rows = await cursor.fetchall()

        columns = [column.name for column in cursor.description]

        jobs = [
            dict(zip(columns, row))
            for row in rows
        ]

    return jobs, total


async def cancel_job(
    connection: AsyncConnection,
    job_id: UUID,
) -> dict | None:

    query = f"""
        UPDATE jobs
        SET
            status = 'CANCELLED',
            completed_at = NOW()
        WHERE id = %(job_id)s
          AND status = 'PENDING'
        RETURNING {JOB_COLUMNS}
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"job_id": job_id},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row)) 

async def retry_job(
    connection: AsyncConnection,
    *,
    job_id: UUID,
):
    query = """
        UPDATE jobs
        SET
            status = 'PENDING',
            last_error = NULL,
            completed_at = NULL,
            locked_by = NULL,
            locked_at = NULL,
            lease_expires_at = NULL
        WHERE id = %(job_id)s
          AND status = 'FAILED'
        RETURNING
            id,
            status,
            attempt_count,
            max_attempts,
            last_error,
            completed_at;
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "job_id": job_id,
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