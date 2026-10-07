"""
SpikeShield Application Settings
Loaded from environment variables and optional .env file.
"""
from __future__ import annotations

import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────
    APP_NAME: str = "SpikeShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── AWS ──────────────────────────────────────────────────
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # ── Elastic Beanstalk ────────────────────────────────────
    EB_APPLICATION_NAME: str = ""
    EB_ENVIRONMENT_NAME: str = ""

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── SQS ──────────────────────────────────────────────────
    SQS_RUNBOOK_QUEUE_URL: str = ""

    # ── Notifications ────────────────────────────────────────
    SLACK_WEBHOOK_URL: str = ""

    # ── Velocity Detector ────────────────────────────────────
    # Window (seconds) for sliding-window RPS calculation
    VELOCITY_WINDOW_SECONDS: int = 60
    # Multiplier over baseline RPS to trigger spike pre-warm
    VELOCITY_SPIKE_THRESHOLD: float = 2.5

    # ── Predictive Pre-Warming ────────────────────────────────
    # How many minutes before a scheduled event to pre-warm the ASG
    PREWARM_MINUTES_BEFORE_EVENT: int = 20

    # ── Error Budget ─────────────────────────────────────────
    # 5xx % above which auto-rollback is triggered
    ERROR_BUDGET_THRESHOLD_PCT: float = 1.0

    # ── CloudWatch Polling ───────────────────────────────────
    CLOUDWATCH_POLLING_INTERVAL_SECONDS: int = 30

    # ── Mock Mode ────────────────────────────────────────────
    # Set True to run fully locally without AWS credentials.
    # All AWS calls return realistic synthetic data.
    MOCK_AWS: bool = True

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def coerce_debug(cls, v: object) -> bool:
        """
        Gracefully handle non-boolean DEBUG values that may be injected by
        system tools (e.g., Node sets DEBUG=release, vite sets DEBUG=vite:*).
        """
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on")
        return bool(v)

    @field_validator("MOCK_AWS", mode="before")
    @classmethod
    def coerce_mock_aws(cls, v: object) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on")
        return bool(v)


# Module-level singleton — import this everywhere
settings = Settings()
