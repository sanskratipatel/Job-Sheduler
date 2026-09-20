import asyncio
import selectors

from database import pool, open_pool, close_pool


async def verify_database():
    await open_pool()

    try:
        async with pool.connection() as connection:

            print("\n=== TABLES ===")

            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                    """
                )

                tables = await cursor.fetchall()

                for table in tables:
                    print(f"✓ {table[0]}")

            print("\n=== JOB TYPES ===")

            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, code, name
                    FROM job_types
                    ORDER BY id;
                    """
                )

                job_types = await cursor.fetchall()

                for job_type in job_types:
                    print(
                        f"✓ {job_type[0]} | "
                        f"{job_type[1]} | "
                        f"{job_type[2]}"
                    )

            print("\n=== JOB STATUSES ===")

            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, code, is_terminal
                    FROM job_statuses
                    ORDER BY id;
                    """
                )

                statuses = await cursor.fetchall()

                for status in statuses:
                    print(
                        f"✓ {status[0]} | "
                        f"{status[1]} | "
                        f"terminal={status[2]}"
                    )

            print("\n=== EXECUTION STATUSES ===")

            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, code, is_terminal
                    FROM execution_statuses
                    ORDER BY id;
                    """
                )

                execution_statuses = await cursor.fetchall()

                for status in execution_statuses:
                    print(
                        f"✓ {status[0]} | "
                        f"{status[1]} | "
                        f"terminal={status[2]}"
                    )

            print("\n=== MIGRATIONS ===")

            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT version, applied_at
                    FROM schema_migrations
                    ORDER BY version;
                    """
                )

                migrations = await cursor.fetchall()

                for migration in migrations:
                    print(
                        f"✓ {migration[0]} | "
                        f"{migration[1]}"
                    )

            print("\nDatabase verification completed successfully.")

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(
        verify_database(),
        loop_factory=lambda: asyncio.SelectorEventLoop(
            selectors.SelectSelector()
        ),
    )