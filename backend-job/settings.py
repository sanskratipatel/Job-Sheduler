from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "job-scheduler-api"
    environment: str = "dev"

    database_uri: str

    db_pool_min_size: int = 1
    db_pool_max_size: int = 5
    db_pool_timeout: float = 10.0
    db_pool_max_idle: float = 120.0
    cors_origins: list[str] = ["*"]
    worker_concurrency: int = 4
    worker_poll_interval_seconds: float = 2.0
    worker_heartbeat_interval_seconds: float = 10.0
    worker_lease_seconds: int = 60
    worker_dead_after_seconds: int = 45
    reaper_interval_seconds: float = 15.0

    retry_base_delay_seconds: float = 5.0
    retry_max_delay_seconds: float = 600.0


settings = Settings()