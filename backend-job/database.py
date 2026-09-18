from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from settings import settings
from utils.errors import DatabaseError
from utils.logger import logger


pool = AsyncConnectionPool(
    settings.database_uri,
    open=False,
    min_size=min(
        settings.db_pool_min_size,
        settings.db_pool_max_size,
    ),
    max_size=settings.db_pool_max_size,
    timeout=settings.db_pool_timeout,
    max_idle=settings.db_pool_max_idle,
    kwargs={
        "application_name": settings.app_name,
    },
)


async def open_pool() -> None:
    await pool.open(wait=True)


async def close_pool() -> None:
    await pool.close()


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    async with pool.connection() as connection:
        yield connection


async def execute_sql(
    sql: str,
    connection: AsyncConnection,
    params: Optional[Dict | Tuple] = None,
    *,
    fetchone: Optional[bool] = None,
    fetchall: bool = True,
    default: Any = None,
    raise_error: bool = True,
    rollback_on_error: bool = True,
    model: Optional[Type[BaseModel]] = None,
) -> Optional[List | Dict | BaseModel]:

    if fetchone is None:
        fetchone = not fetchall

    try:
        async with connection.cursor(
            row_factory=dict_row
        ) as cursor:

            await cursor.execute(sql, params)

            if cursor.description is None:
                return None

            if fetchone:
                row = await cursor.fetchone()

                if row is None:
                    return None

                return model(**row) if model else row

            rows = await cursor.fetchall()

            if model:
                return [
                    model(**row)
                    for row in rows
                ]

            return rows

    except Exception as error:
        logger.exception(error.__class__.__name__)

        if rollback_on_error:
            await connection.rollback()

        if raise_error:
            raise DatabaseError(str(error)) from error

        return default