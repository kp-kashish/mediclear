from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str

    OPENAI_API_KEY: str

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "eu-central-1"
    S3_BUCKET_NAME: str

    DATABASE_URL: str

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"


settings = Settings()