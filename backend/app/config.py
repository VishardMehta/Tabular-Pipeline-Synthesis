"""Settings loaded from the environment, plus the execution boot guard."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Field names mirror .env.example, lowercased."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str = ""
    llm_model: str = "gemini-3.6-flash"
    llm_timeout_s: int = 60

    deployment_env: str = "local"
    enable_local_execution: bool = False
    execution_timeout_s: int = 60
    execution_sample_rows: int = 500
    runner_python: str = ".venv-runner/bin/python"

    upload_dir: str = "./data/uploads"
    db_path: str = "./data/app.db"
    dataset_ttl_hours: int = 24
    max_file_mb: int = 50
    max_cols: int = 1000

    cors_origins: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed origins.",
    )

    @field_validator("deployment_env")
    @classmethod
    def _known_environment(cls, value: str) -> str:
        if value not in {"local", "hosted"}:
            raise ValueError("DEPLOYMENT_ENV must be 'local' or 'hosted'")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

# Boot guard, not a convention. Local execution runs generated code in a
# subprocess with no container boundary around it, which is acceptable on a
# developer's own machine and is not acceptable anywhere else. Failing at import
# time makes a misconfigured deployment impossible to start rather than
# quietly dangerous.
if settings.enable_local_execution and settings.deployment_env != "local":
    raise RuntimeError("ENABLE_LOCAL_EXECUTION is only permitted when DEPLOYMENT_ENV=local")
