from fastapi import FastAPI
from jobs.routes import router as jobs_router
from database import get_db_connection
from lifespan import lifespan
from utils.logger import logger
from fastapi import FastAPI 
from settings import settings
from fastapi.middleware.cors import CORSMiddleware
from dashboard.routes import router as dashboard_router
from workers.routes import router as workers_router
from schedules.routes import router as schedule_router
from executions.routes import router as excution_router
app = FastAPI(
    title="Job Scheduler API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router) 
app.include_router(workers_router) 
app.include_router(schedule_router)
app.include_router(excution_router)
app.include_router(dashboard_router)
@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


@app.get("/ready")
async def ready():
    try:
        async for connection in get_db_connection():
            await connection.execute("SELECT 1")
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as error:
        logger.exception("Database readiness check failed")

        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(error),
        }