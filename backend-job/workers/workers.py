import asyncio
import os
import socket
import traceback
from time import monotonic
from uuid import UUID

from database import pool
from executions.query import (
    complete_execution,
    create_execution,
    fail_execution,
)
from handlers.registry import get_handler
from settings import settings
from utils.logger import logger
from workers.query import (
    claim_job,
    fail_job,
    reap_expired_jobs,
    renew_job_lease,
    mark_dead_workers,
    succeed_job,
)


class Worker:
    def __init__(self):
        self.worker_id: UUID | None = None

        self.hostname = socket.gethostname()
        self.pid = os.getpid()

        self.concurrency = settings.worker_concurrency
        self.lease_seconds = settings.worker_lease_seconds

        self.running = True

        self.semaphore = asyncio.Semaphore(
            self.concurrency
        )

        self.running_tasks: set[asyncio.Task] = set()

    # =========================================================
    # WORKER REGISTRATION
    # =========================================================

    async def register(self) -> None:
        query = """
            INSERT INTO workers (
                hostname,
                pid,
                status,
                concurrency,
                version,
                git_sha
            )
            VALUES (
                %(hostname)s,
                %(pid)s,
                'ACTIVE',
                %(concurrency)s,
                %(version)s,
                %(git_sha)s
            )
            RETURNING id
        """

        params = {
            "hostname": self.hostname,
            "pid": self.pid,
            "concurrency": self.concurrency,
            "version": "1.0.0",
            "git_sha": None,
        }

        async with pool.connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    query,
                    params,
                )

                row = await cursor.fetchone()

            await connection.commit()

        if row is None:
            raise RuntimeError(
                "Worker registration failed."
            )

        self.worker_id = row[0]

        logger.info(
            "Worker registered | id=%s | hostname=%s | pid=%s | concurrency=%s",
            self.worker_id,
            self.hostname,
            self.pid,
            self.concurrency,
        )

    # =========================================================
    # HEARTBEAT
    # =========================================================

    async def heartbeat(self) -> None:
        if self.worker_id is None:
            return

        query = """
            UPDATE workers
            SET last_heartbeat_at = NOW()
            WHERE id = %(worker_id)s
              AND status IN ('ACTIVE', 'DRAINING')
        """

        async with pool.connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    query,
                    {
                        "worker_id": self.worker_id,
                    },
                )

            await connection.commit()

    async def heartbeat_loop(self) -> None:
        while self.running:
            try:
                await self.heartbeat()

            except Exception:
                logger.exception(
                    "Worker heartbeat failed."
                )

            await asyncio.sleep(
                settings.worker_heartbeat_interval_seconds
            )

    # =========================================================
    # CLAIM JOB
    # =========================================================

    async def claim_one_job(self):
        if self.worker_id is None:
            return None

        async with pool.connection() as connection:

            job = await claim_job(
                connection,
                worker_id=self.worker_id,
                lease_seconds=self.lease_seconds,
            )

            if job is None:
                await connection.rollback()
                return None

            await connection.commit()

            return job

    # =========================================================
    # JOB LEASE RENEWAL
    # =========================================================

    async def renew_job_lease_loop(
        self,
        job_id: UUID,
    ) -> None:

        interval = max(
            1,
            self.lease_seconds // 3,
        )

        try:
            while True:

                await asyncio.sleep(interval)

                if self.worker_id is None:
                    return

                async with pool.connection() as connection:

                    result = await renew_job_lease(
                        connection,
                        job_id=job_id,
                        worker_id=self.worker_id,
                        lease_seconds=self.lease_seconds,
                    )

                    await connection.commit()

                if result is None:

                    logger.warning(
                        "Lease renewal stopped | job_id=%s | worker_id=%s",
                        job_id,
                        self.worker_id,
                    )

                    return

                logger.debug(
                    "Job lease renewed | job_id=%s | expires_at=%s",
                    job_id,
                    result["lease_expires_at"],
                )

        except asyncio.CancelledError:

            logger.debug(
                "Lease renewal cancelled | job_id=%s",
                job_id,
            )

            raise

        except Exception:

            logger.exception(
                "Lease renewal failed | job_id=%s",
                job_id,
            )

    # =========================================================
    # EXECUTE JOB
    # =========================================================

    async def execute_job(
        self,
        job: dict,
    ) -> None:

        async with self.semaphore:

            if self.worker_id is None:
                raise RuntimeError(
                    "Worker is not registered."
                )

            job_id = job["id"]

            attempt_number = job[
                "attempt_count"
            ]

            logger.info(
                "Executing job | job_id=%s | type=%s | attempt=%s",
                job_id,
                job["job_type"],
                attempt_number,
            )

            execution = None
            lease_task = None

            start_time = monotonic()

            try:

                # ---------------------------------------------
                # CREATE EXECUTION
                # ---------------------------------------------

                async with pool.connection() as connection:

                    execution = await create_execution(
                        connection,
                        job_id=job_id,
                        worker_id=self.worker_id,
                        attempt_number=attempt_number,
                    )

                    if execution is None:

                        await connection.rollback()

                        raise RuntimeError(
                            "Failed to create job execution."
                        )

                    await connection.commit()

                # ---------------------------------------------
                # START LEASE RENEWAL
                # ---------------------------------------------

                lease_task = asyncio.create_task(
                    self.renew_job_lease_loop(
                        job_id
                    )
                )

                # ---------------------------------------------
                # GET HANDLER
                # ---------------------------------------------

                handler = get_handler(
                    job["job_type"]
                )

                # ---------------------------------------------
                # EXECUTE HANDLER
                # ---------------------------------------------

                result = await asyncio.wait_for(
                    handler.run(
                        job["payload"]
                    ),
                    timeout=job[
                        "timeout_seconds"
                    ],
                )

                duration_ms = int(
                    (
                        monotonic()
                        - start_time
                    )
                    * 1000
                )

                # ---------------------------------------------
                # COMPLETE EXECUTION + JOB
                # ---------------------------------------------

                async with pool.connection() as connection:

                    completed = await complete_execution(
                        connection,
                        execution_id=execution[
                            "id"
                        ],
                        output=result,
                        duration_ms=duration_ms,
                    )

                    if completed is None:

                        await connection.rollback()

                        raise RuntimeError(
                            "Failed to complete execution."
                        )

                    job_completed = await succeed_job(
                        connection,
                        job_id=job_id,
                        worker_id=self.worker_id,
                    )

                    if job_completed is None:

                        await connection.rollback()

                        raise RuntimeError(
                            "Failed to mark job as succeeded."
                        )

                    await connection.commit()

                logger.info(
                    "Job completed | job_id=%s | duration_ms=%s",
                    job_id,
                    duration_ms,
                )

            except asyncio.TimeoutError:

                duration_ms = int(
                    (
                        monotonic()
                        - start_time
                    )
                    * 1000
                )

                await self.handle_job_failure(
                    job=job,
                    execution=execution,
                    error_message=(
                        f"Job timed out after "
                        f"{job['timeout_seconds']} seconds."
                    ),
                    error_traceback=None,
                    duration_ms=duration_ms,
                )

            except Exception as error:

                duration_ms = int(
                    (
                        monotonic()
                        - start_time
                    )
                    * 1000
                )

                await self.handle_job_failure(
                    job=job,
                    execution=execution,
                    error_message=str(error),
                    error_traceback=traceback.format_exc(),
                    duration_ms=duration_ms,
                )

            finally:

                # ---------------------------------------------
                # STOP LEASE RENEWAL
                # ---------------------------------------------

                if lease_task is not None:

                    lease_task.cancel()

                    try:
                        await lease_task

                    except asyncio.CancelledError:
                        pass

    # =========================================================
    # FAILURE
    # =========================================================

    async def handle_job_failure(
        self,
        *,
        job: dict,
        execution: dict | None,
        error_message: str,
        error_traceback: str | None,
        duration_ms: int,
    ) -> None:

        job_id = job["id"]

        logger.error(
            "Job failed | job_id=%s | error=%s",
            job_id,
            error_message,
        )

        async with pool.connection() as connection:

            if execution is not None:

                failed_execution = await fail_execution(
                    connection,
                    execution_id=execution[
                        "id"
                    ],
                    error_message=error_message,
                    error_traceback=error_traceback,
                    duration_ms=duration_ms,
                )

                if failed_execution is None:

                    await connection.rollback()

                    logger.error(
                        "Failed to update execution | execution_id=%s",
                        execution["id"],
                    )

                    return

            job_result = await fail_job(
                connection,
                job_id=job_id,
                worker_id=self.worker_id,
                error_message=error_message,
            )

            if job_result is None:

                await connection.rollback()

                logger.error(
                    "Failed to update job | job_id=%s",
                    job_id,
                )

                return

            await connection.commit()

        logger.info(
            "Job failure handled | job_id=%s | status=%s | attempt=%s/%s",
            job_id,
            job_result["status"],
            job_result["attempt_count"],
            job_result["max_attempts"],
        )

    # =========================================================
    # JOB POLLING
    # =========================================================

    async def poll_loop(self) -> None:

        while self.running:

            try:

                # Don't claim more jobs than
                # our concurrency allows.

                if (
                    len(self.running_tasks)
                    >= self.concurrency
                ):

                    await asyncio.sleep(
                        0.1
                    )

                    continue

                job = await self.claim_one_job()

                if job is None:

                    await asyncio.sleep(
                        settings.worker_poll_interval_seconds
                    )

                    continue

                task = asyncio.create_task(
                    self.execute_job(job)
                )

                self.running_tasks.add(
                    task
                )

                task.add_done_callback(
                    self.running_tasks.discard
                )

            except asyncio.CancelledError:

                raise

            except Exception:

                logger.exception(
                    "Worker polling failed."
                )

                await asyncio.sleep(
                    settings.worker_poll_interval_seconds
                )

    # =========================================================
    # REAPER
    # =========================================================

    async def reaper_loop(self) -> None:

        while self.running:

            try:

                async with pool.connection() as connection:

                    expired_jobs = await reap_expired_jobs(
                        connection
                    )

                    dead_workers = await mark_dead_workers(
                        connection,
                        dead_after_seconds=(
                            settings.worker_dead_after_seconds
                        ),
                    )

                    await connection.commit()

                for job in expired_jobs:

                    logger.warning(
                        "Expired job recovered | job_id=%s | status=%s",
                        job["id"],
                        job["status"],
                    )

                for worker in dead_workers:

                    logger.warning(
                        "Worker marked DEAD | worker_id=%s | hostname=%s | pid=%s",
                        worker["id"],
                        worker["hostname"],
                        worker["pid"],
                    )

            except Exception:

                logger.exception(
                    "Reaper failed."
                )

            await asyncio.sleep(
                settings.reaper_interval_seconds
            )

    # =========================================================
    # SHUTDOWN
    # =========================================================

    async def shutdown(self) -> None:

        self.running = False

        # Wait for currently running jobs.

        if self.running_tasks:

            logger.info(
                "Waiting for %s running jobs...",
                len(self.running_tasks),
            )

            await asyncio.gather(
                *self.running_tasks,
                return_exceptions=True,
            )

        if self.worker_id is None:
            return

        query = """
            UPDATE workers
            SET
                status = 'STOPPED',
                stopped_at = NOW()
            WHERE id = %(worker_id)s
        """

        async with pool.connection() as connection:

            async with connection.cursor() as cursor:

                await cursor.execute(
                    query,
                    {
                        "worker_id": self.worker_id
                    },
                )

            await connection.commit()

        logger.info(
            "Worker stopped | id=%s",
            self.worker_id,
        )

    # =========================================================
    # MAIN WORKER LOOP
    # =========================================================

    async def run(self) -> None:

        await self.register()

        heartbeat_task = asyncio.create_task(
            self.heartbeat_loop()
        )

        poll_task = asyncio.create_task(
            self.poll_loop()
        )

        reaper_task = asyncio.create_task(
            self.reaper_loop()
        )

        try:

            await asyncio.gather(
                poll_task,
                reaper_task,
            )

        except asyncio.CancelledError:

            logger.info(
                "Worker task cancelled."
            )

        finally:

            self.running = False

            heartbeat_task.cancel()
            poll_task.cancel()
            reaper_task.cancel()

            for task in (
                heartbeat_task,
                poll_task,
                reaper_task,
            ):

                try:
                    await task

                except asyncio.CancelledError:
                    pass

            await self.shutdown()


async def main():

    await pool.open(
        wait=True
    )

    worker = Worker()

    try:

        await worker.run()

    except KeyboardInterrupt:

        logger.info(
            "Worker interrupted by user."
        )

    finally:

        await pool.close()


if __name__ == "__main__":

    asyncio.run(
        main(),
        loop_factory=lambda: asyncio.SelectorEventLoop()
    )