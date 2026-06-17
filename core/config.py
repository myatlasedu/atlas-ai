from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: int

    OLLAMA_BASE_URL: str

    INTERNAL_API_KEY: str

    OLLAMA_MODEL: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()