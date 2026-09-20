import asyncio
import selectors

from psycopg import AsyncConnection

from settings import settings


RESET_SQL = """
DROP TABLE IF EXISTS job_executions CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS job_schedules CASCADE;
DROP TABLE IF EXISTS workers CASCADE;
DROP TABLE IF EXISTS job_types CASCADE;
DROP TABLE IF EXISTS schema_migrations CASCADE;

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
"""


async def reset_database() -> None:
    print("Starting database reset...")

    async with await AsyncConnection.connect(
        settings.database_uri
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(RESET_SQL)

        await connection.commit()

    print("Database reset completed successfully.")


if __name__ == "__main__":
    asyncio.run(
        reset_database(),
        loop_factory=lambda: asyncio.SelectorEventLoop(
            selectors.SelectSelector()
        ),
    )