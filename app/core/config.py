from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://board:board_password@localhost:5433/board"
    SECRET_KEY: str = "dev-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
