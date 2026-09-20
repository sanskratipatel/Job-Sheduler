from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import close_pool, open_pool
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Job Scheduler API...")

    await open_pool()

    logger.info("Database connection pool opened")

    try:
        yield
    finally:
        logger.info("Shutting down Job Scheduler API...")

        await close_pool()

        logger.info("Database connection pool closed")