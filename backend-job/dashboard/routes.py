from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from database import get_db_connection
from .query import get_dashboard_stats
from .response import DashboardStatsResponse


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


async def get_connection():
    async for connection in get_db_connection():
        yield connection


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
)
async def dashboard_stats(
    connection: AsyncConnection = Depends(get_connection),
):
    return await get_dashboard_stats(connection)