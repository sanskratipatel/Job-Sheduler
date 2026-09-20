from pathlib import Path

from database import pool, open_pool, close_pool
from utils.logger import logger

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
async def ensure_migration_table():
    async with pool.connection() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
        await connection.commit()


async def get_applied_migrations():
    async with pool.connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT version
                FROM schema_migrations
                ORDER BY version;
                """
            )

            rows = await cursor.fetchall()

            return {row[0] for row in rows}


async def apply_migration(
    migration_file: Path,
):
    version = migration_file.name

    logger.info(f"Applying migration: {version}")

    sql = migration_file.read_text(
        encoding="utf-8"
    )

    async with pool.connection() as connection:

        try:
            await connection.execute(sql)

            await connection.execute(
                """
                INSERT INTO schema_migrations (version)
                VALUES (%s)
                ON CONFLICT (version) DO NOTHING;
                """,
                (version,),
            )

            await connection.commit()

            logger.info(
                f"Migration applied successfully: {version}"
            )

        except Exception:
            await connection.rollback()

            logger.exception(
                f"Migration failed: {version}"
            )

            raise


async def run_migrations():
    await open_pool()

    try:
        await ensure_migration_table()

        applied_migrations = (
            await get_applied_migrations()
        )

        migration_files = sorted(
            MIGRATIONS_DIR.glob("*.sql")
        )

        if not migration_files:
            logger.info("No migration files found.")
            return

        for migration_file in migration_files:

            version = migration_file.name

            if version in applied_migrations:
                logger.info(
                    f"Skipping already applied migration: {version}"
                )
                continue

            await apply_migration(
                migration_file
            )

        logger.info("Database migrations completed.")

    finally:
        await close_pool()

if __name__ == "__main__":
    import asyncio
    import selectors

    asyncio.run(
        run_migrations(),
        loop_factory=lambda: asyncio.SelectorEventLoop(
            selectors.SelectSelector()
        ),
    )