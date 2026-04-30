import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_from_secret_manager() -> None:
    settings_name = os.environ.get("SETTINGS_NAME")
    if not settings_name:
        return

    from google.cloud import secretmanager

    project_id = os.environ.get("PROJECT_ID")
    if not project_id:
        raise RuntimeError("PROJECT_ID env var required when SETTINGS_NAME is set")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("utf-8").strip()

    if payload.startswith("{"):
        values = json.loads(payload)
    else:
        values = {}
        for line in payload.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")

    # Only set values not already present in the environment
    for key, value in values.items():
        os.environ.setdefault(key, value)


_load_from_secret_manager()


class Settings(BaseSettings):
    """Application settings loaded from environment variables or GCP Secret Manager."""

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # Africa's Talking
    AT_USERNAME: str
    AT_API_KEY: str
    AT_SHORTCODE: str = "*384#"

    # Admin Seed
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
