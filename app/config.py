# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://medivision:medivision_dev_pass@localhost:5432/medivision_dev"
    )
    jwt_secret_key: str = "dev-secret-change-in-prod"
    storage_bucket_private: str = "medivision-prescriptions-private"
    firebase_credentials_path: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()