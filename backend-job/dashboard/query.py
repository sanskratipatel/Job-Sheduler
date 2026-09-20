from psycopg import AsyncConnection


async def get_dashboard_stats(
    connection: AsyncConnection,
) -> dict:
    job_query = """
        SELECT
            COUNT(*) AS total_jobs,

            COUNT(*) FILTER (
                WHERE status = 'PENDING'
            ) AS pending_jobs,

            COUNT(*) FILTER (
                WHERE status = 'PROCESSING'
            ) AS processing_jobs,

            COUNT(*) FILTER (
                WHERE status = 'SUCCEEDED'
            ) AS succeeded_jobs,

            COUNT(*) FILTER (
                WHERE status = 'FAILED'
            ) AS failed_jobs,

            COUNT(*) FILTER (
                WHERE status = 'CANCELLED'
            ) AS cancelled_jobs

        FROM jobs;
    """

    async with connection.cursor() as cursor:
        await cursor.execute(job_query)
        job_stats = await cursor.fetchone()

    worker_query = """
        SELECT COUNT(*)
        FROM workers
        WHERE status = 'ACTIVE';
    """

    async with connection.cursor() as cursor:
        await cursor.execute(worker_query)
        worker_stats = await cursor.fetchone()

    schedule_query = """
        SELECT COUNT(*)
        FROM job_schedules
        WHERE status = 'ACTIVE';
    """

    async with connection.cursor() as cursor:
        await cursor.execute(schedule_query)
        schedule_stats = await cursor.fetchone()

    return {
        "total_jobs": job_stats[0],
        "pending_jobs": job_stats[1],
        "processing_jobs": job_stats[2],
        "succeeded_jobs": job_stats[3],
        "failed_jobs": job_stats[4],
        "cancelled_jobs": job_stats[5],
        "active_workers": worker_stats[0],
        "active_schedules": schedule_stats[0],
    }