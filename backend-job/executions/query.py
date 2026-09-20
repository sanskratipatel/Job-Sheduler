from uuid import UUID

from psycopg.types.json import Jsonb


EXECUTION_COLUMNS = """
    id,
    job_id,
    worker_id,
    attempt_number,
    status,
    started_at,
    finished_at,
    duration_ms,
    error_message,
    error_traceback,
    output,
    created_at
"""


async def create_execution(
    connection,
    *,
    job_id: UUID,
    worker_id: UUID,
    attempt_number: int,
):
    query = f"""
        INSERT INTO job_executions (
            job_id,
            worker_id,
            attempt_number,
            status
        )
        VALUES (
            %(job_id)s,
            %(worker_id)s,
            %(attempt_number)s,
            'RUNNING'
        )
        RETURNING {EXECUTION_COLUMNS}
    """

    params = {
        "job_id": job_id,
        "worker_id": worker_id,
        "attempt_number": attempt_number,
    }

    async with connection.cursor() as cursor:
        await cursor.execute(query, params)

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def complete_execution(
    connection,
    *,
    execution_id: UUID,
    output: dict,
    duration_ms: int,
):
    query = f"""
        UPDATE job_executions
        SET
            status = 'SUCCEEDED',
            finished_at = NOW(),
            duration_ms = %(duration_ms)s,
            output = %(output)s
        WHERE id = %(execution_id)s
          AND status = 'RUNNING'
        RETURNING {EXECUTION_COLUMNS}
    """

    params = {
        "execution_id": execution_id,
        "duration_ms": duration_ms,
        "output": Jsonb(output),
    }

    async with connection.cursor() as cursor:
        await cursor.execute(query, params)

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def fail_execution(
    connection,
    *,
    execution_id: UUID,
    error_message: str,
    error_traceback: str | None,
    duration_ms: int,
):
    query = f"""
        UPDATE job_executions
        SET
            status = 'FAILED',
            finished_at = NOW(),
            duration_ms = %(duration_ms)s,
            error_message = %(error_message)s,
            error_traceback = %(error_traceback)s
        WHERE id = %(execution_id)s
          AND status = 'RUNNING'
        RETURNING {EXECUTION_COLUMNS}
    """

    params = {
        "execution_id": execution_id,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "error_traceback": error_traceback,
    }

    async with connection.cursor() as cursor:
        await cursor.execute(query, params)

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def get_execution_by_id(
    connection,
    execution_id: UUID,
):
    query = f"""
        SELECT {EXECUTION_COLUMNS}
        FROM job_executions
        WHERE id = %(execution_id)s
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"execution_id": execution_id},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(zip(columns, row))


async def list_executions(
    connection,
    *,
    job_id: UUID | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    conditions = []
    params = {
        "limit": limit,
        "offset": offset,
    }

    if job_id:
        conditions.append(
            "job_id = %(job_id)s"
        )
        params["job_id"] = job_id

    if status:
        conditions.append(
            "status = %(status)s"
        )
        params["status"] = status

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE " + " AND ".join(conditions)
        )

    count_query = f"""
        SELECT COUNT(*)
        FROM job_executions
        {where_clause}
    """

    data_query = f"""
        SELECT {EXECUTION_COLUMNS}
        FROM job_executions
        {where_clause}
        ORDER BY started_at DESC, id DESC
        LIMIT %(limit)s
        OFFSET %(offset)s
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            count_query,
            params,
        )

        count_row = await cursor.fetchone()
        total = count_row[0]

        await cursor.execute(
            data_query,
            params,
        )

        rows = await cursor.fetchall()

        columns = [
            column.name
            for column in cursor.description
        ]

        executions = [
            dict(zip(columns, row))
            for row in rows
        ]

    return executions, total  


async def list_executions_by_job(
    connection: AsyncConnection,
    *,
    job_id: UUID,
    limit: int = 50,
    offset: int = 0,
):
    count_query = """
        SELECT COUNT(*) AS total
        FROM job_executions
        WHERE job_id = %(job_id)s;
    """

    list_query = f"""
        SELECT {EXECUTION_COLUMNS}
        FROM job_executions
        WHERE job_id = %(job_id)s
        ORDER BY attempt_number DESC
        LIMIT %(limit)s
        OFFSET %(offset)s;
    """

    params = {
        "job_id": job_id,
        "limit": limit,
        "offset": offset,
    }

    async with connection.cursor() as cursor:

        await cursor.execute(
            count_query,
            params,
        )

        count_row = await cursor.fetchone()

        total = count_row[0] if count_row else 0

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