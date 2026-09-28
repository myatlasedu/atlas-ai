from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str

    APP_ENV: str = "production"

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: int

    OLLAMA_BASE_URL: str

    INTERNAL_API_KEY: str

    LLM_BASE_URL: str
    LLM_MODEL: str
    LLM_API_KEY: str

    OLLAMA_MODEL: str
    OLLAMA_TIMEOUT_SECONDS:int = 60
    REQUEST_LOCK_TTL_SECONDS: int = 120

    # Environments where the caller-trusted session API may be exposed.
    SESSION_API_ENVIRONMENTS: frozenset[str] = frozenset(
        {"local", "development", "dev", "staging", "test"}
    )

    @property
    def is_production(self) -> bool:

        return self.APP_ENV.strip().lower() not in self.SESSION_API_ENVIRONMENTS

    @property
    def session_api_enabled(self) -> bool:
        
        return not self.is_production

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()