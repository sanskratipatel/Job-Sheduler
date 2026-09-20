from uuid import UUID


WORKER_COLUMNS = """
    id,
    hostname,
    pid,
    status,
    concurrency,
    version,
    git_sha,
    started_at,
    last_heartbeat_at,
    stopped_at,
    created_at,
    updated_at
"""


async def register_worker(
    connection,
    *,
    hostname,
    pid,
    concurrency,
    version,
    git_sha,
):
    query = f"""
        INSERT INTO workers (
            hostname,
            pid,
            concurrency,
            version,
            git_sha
        )
        VALUES (
            %(hostname)s,
            %(pid)s,
            %(concurrency)s,
            %(version)s,
            %(git_sha)s
        )
        RETURNING {WORKER_COLUMNS}
    """

    params = {
        "hostname": hostname,
        "pid": pid,
        "concurrency": concurrency,
        "version": version,
        "git_sha": git_sha,
    }

    async with connection.cursor() as cursor:
        await cursor.execute(query, params)

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def list_workers(
    connection,
    *,
    status=None,
):
    where_clause = ""
    params = {}

    if status:
        where_clause = "WHERE status = %(status)s"
        params["status"] = status

    count_query = f"""
        SELECT COUNT(*)
        FROM workers
        {where_clause}
    """

    data_query = f"""
        SELECT {WORKER_COLUMNS}
        FROM workers
        {where_clause}
        ORDER BY started_at DESC, id DESC
    """

    async with connection.cursor() as cursor:
        await cursor.execute(count_query, params)

        count_row = await cursor.fetchone()
        total = count_row[0]

        await cursor.execute(data_query, params)

        rows = await cursor.fetchall()

        columns = [column.name for column in cursor.description]

        workers = [
            dict(zip(columns, row))
            for row in rows
        ]

    return workers, total


async def get_worker_by_id(
    connection,
    worker_id: UUID,
):
    query = f"""
        SELECT {WORKER_COLUMNS}
        FROM workers
        WHERE id = %(worker_id)s
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"worker_id": worker_id},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def heartbeat_worker(
    connection,
    worker_id: UUID,
):
    query = """
        UPDATE workers
        SET
            last_heartbeat_at = NOW()
        WHERE id = %(worker_id)s
          AND status IN ('ACTIVE', 'DRAINING')
        RETURNING
            id,
            status,
            last_heartbeat_at
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"worker_id": worker_id},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))


async def stop_worker(
    connection,
    worker_id: UUID,
):
    query = f"""
        UPDATE workers
        SET
            status = 'STOPPED',
            stopped_at = NOW()
        WHERE id = %(worker_id)s
          AND status <> 'STOPPED'
        RETURNING {WORKER_COLUMNS}
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {"worker_id": worker_id},
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]

        return dict(zip(columns, row))  


from uuid import UUID


async def claim_job(
    connection,
    *,
    worker_id: UUID,
    lease_seconds: int,
):
    query = """
        WITH next_job AS (
            SELECT id
            FROM jobs
            WHERE status = 'PENDING'
              AND scheduled_at <= NOW()
              AND attempt_count < max_attempts
            ORDER BY
                priority DESC,
                scheduled_at ASC,
                id ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        UPDATE jobs
        SET
            status = 'PROCESSING',
            locked_by = %(worker_id)s,
            locked_at = NOW(),
            lease_expires_at = NOW() + (
                %(lease_seconds)s * INTERVAL '1 second'
            ),
            attempt_count = attempt_count + 1,
            started_at = COALESCE(started_at, NOW())
        WHERE id IN (
            SELECT id
            FROM next_job
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

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "worker_id": worker_id,
                "lease_seconds": lease_seconds,
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


    
# async def reap_expired_jobs(
#     connection,
# ):
#     query = """
#         UPDATE jobs
#         SET
#             status = CASE
#                 WHEN attempt_count < max_attempts
#                     THEN 'PENDING'
#                 ELSE 'FAILED'
#             END,
#             last_error = 'Worker lease expired.',
#             locked_by = NULL,
#             locked_at = NULL,
#             lease_expires_at = NULL,
#             completed_at = CASE
#                 WHEN attempt_count >= max_attempts
#                     THEN NOW()
#                 ELSE NULL
#             END
#         WHERE status = 'PROCESSING'
#           AND lease_expires_at <= NOW()
#         RETURNING
#             id,
#             status,
#             attempt_count,
#             max_attempts;
#     """

#     async with connection.cursor() as cursor:
#         await cursor.execute(query)

#         rows = await cursor.fetchall()

#         if not rows:
#             return []

#         columns = [
#             column.name
#             for column in cursor.description
#         ]

#         return [
#             dict(zip(columns, row))
#             for row in rows
#         ]



async def reap_expired_jobs(connection):
    query = """
        WITH expired_jobs AS (
            SELECT
                id,
                attempt_count
            FROM jobs
            WHERE status = 'PROCESSING'
              AND lease_expires_at <= NOW()
            FOR UPDATE SKIP LOCKED
        ),
        abandoned_executions AS (
            UPDATE job_executions e
            SET
                status = 'ABANDONED',
                finished_at = NOW(),
                duration_ms = CASE
                    WHEN e.started_at IS NOT NULL
                    THEN EXTRACT(
                        EPOCH FROM (NOW() - e.started_at)
                    ) * 1000
                    ELSE NULL
                END,
                error_message = 'Worker lease expired.'
            FROM expired_jobs j
            WHERE e.job_id = j.id
              AND e.attempt_number = j.attempt_count
              AND e.status = 'RUNNING'
            RETURNING e.id
        )
        UPDATE jobs j
        SET
            status = CASE
                WHEN j.attempt_count < j.max_attempts
                THEN 'PENDING'
                ELSE 'FAILED'
            END,
            last_error = 'Worker lease expired.',
            locked_by = NULL,
            locked_at = NULL,
            lease_expires_at = NULL,
            completed_at = CASE
                WHEN j.attempt_count >= j.max_attempts
                THEN NOW()
                ELSE NULL
            END
        FROM expired_jobs e
        WHERE j.id = e.id
        RETURNING
            j.id,
            j.status,
            j.attempt_count,
            j.max_attempts;
    """

    async with connection.cursor() as cursor:
        await cursor.execute(query)

        rows = await cursor.fetchall()

        columns = [column.name for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in rows
        ]

async def mark_dead_workers(
    connection,
    *,
    dead_after_seconds: int,
):
    query = """
        UPDATE workers
        SET
            status = 'DEAD'
        WHERE status IN ('ACTIVE', 'DRAINING')
          AND last_heartbeat_at <
              NOW() - (
                  %(dead_after_seconds)s
                  * INTERVAL '1 second'
              )
        RETURNING id, hostname, pid;
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "dead_after_seconds": dead_after_seconds,
            },
        )

        rows = await cursor.fetchall()

        if not rows:
            return []

        columns = [
            column.name
            for column in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ] 
async def renew_job_lease(
    connection,
    *,
    job_id: UUID,
    worker_id: UUID,
    lease_seconds: int,
):
    query = """
        UPDATE jobs
        SET
            lease_expires_at = NOW() + (
                %(lease_seconds)s * INTERVAL '1 second'
            )
        WHERE id = %(job_id)s
          AND status = 'PROCESSING'
          AND locked_by = %(worker_id)s
        RETURNING id, lease_expires_at;
    """

    async with connection.cursor() as cursor:
        await cursor.execute(
            query,
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "lease_seconds": lease_seconds,
            },
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [column.name for column in cursor.description]
        return dict(zip(columns, row)) 

async def renew_job_lease(
    connection,
    *,
    job_id: UUID,
    worker_id: UUID,
    lease_seconds: int,
):
    query = """
        UPDATE jobs
        SET
            lease_expires_at = NOW() + (
                %(lease_seconds)s * INTERVAL '1 second'
            )
        WHERE id = %(job_id)s
          AND status = 'PROCESSING'
          AND locked_by = %(worker_id)s
        RETURNING id, lease_expires_at;
    """

    async with connection.cursor() as cursor:

        await cursor.execute(
            query,
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "lease_seconds": lease_seconds,
            },
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

        return dict(
            zip(columns, row)
        ) 
async def list_worker_jobs(
    connection: AsyncConnection,
    *,
    worker_id: UUID,
    limit: int = 50,
    offset: int = 0,
):
    query = """
        SELECT
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
        FROM jobs
        WHERE locked_by = %(worker_id)s
        ORDER BY locked_at DESC
        LIMIT %(limit)s
        OFFSET %(offset)s;
    """

    count_query = """
        SELECT COUNT(*) AS total
        FROM jobs
        WHERE locked_by = %(worker_id)s;
    """

    params = {
        "worker_id": worker_id,
        "limit": limit,
        "offset": offset,
    }

    async with connection.cursor() as cursor:

        await cursor.execute(
            count_query,
            {
                "worker_id": worker_id,
            },
        )

        count_row = await cursor.fetchone()

        total = count_row[0] if count_row else 0

        await cursor.execute(
            query,
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