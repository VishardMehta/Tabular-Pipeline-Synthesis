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

    # Several keys are supported because the free tier's per-day quota is per
    # project, not per caller: one key runs out long before a working session
    # does. GOOGLE_API_KEY stays the single-key name so existing setups keep
    # working; the numbered ones are additive.
    google_api_key: str = ""
    google_api_key1: str = ""
    google_api_key2: str = ""
    google_api_key3: str = ""
    llm_model: str = "gemini-3.1-flash-lite"
    llm_timeout_s: int = 60

    deployment_env: str = "local"

    # Stage-6 placeholders. Nothing reads the three below, and
    # enable_local_execution gates only the boot assertion at the bottom of this
    # file - there is no execution module, and scikit-learn is not a backend
    # dependency. They are kept rather than deleted because the boot guard is a
    # genuine fail-closed assertion worth having in place before the feature
    # lands. Do not read this block as "execution exists and is switched off".
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

    @property
    def google_api_key_list(self) -> list[str]:
        """Every configured key, in declaration order, deduplicated.

        Order is stable so the rotation cursor in llm.py means the same thing
        across a restart. Duplicates are dropped because two entries holding
        the same key would look like two quotas and are one - the rotation
        would "fail over" onto the key that just returned 429.
        """
        candidates = [
            self.google_api_key,
            self.google_api_key1,
            self.google_api_key2,
            self.google_api_key3,
        ]
        seen: set[str] = set()
        keys: list[str] = []
        for candidate in candidates:
            key = candidate.strip()
            if key and key not in seen:
                seen.add(key)
                keys.append(key)
        return keys


settings = Settings()

# Boot guard, not a convention. Local execution runs generated code in a
# subprocess with no container boundary around it, which is acceptable on a
# developer's own machine and is not acceptable anywhere else. Failing at import
# time makes a misconfigured deployment impossible to start rather than
# quietly dangerous.
if settings.enable_local_execution and settings.deployment_env != "local":
    raise RuntimeError("ENABLE_LOCAL_EXECUTION is only permitted when DEPLOYMENT_ENV=local")
