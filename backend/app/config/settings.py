from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./mt5_bonus.db"
    SECRET_KEY: str = "dev-secret-key-not-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # MT5 Manager Web API (leave blank for mock gateway)
    MT5_SERVER_URL: Optional[str] = None
    MT5_MANAGER_LOGIN: Optional[str] = None
    MT5_MANAGER_PASSWORD: Optional[str] = None
    MT5_API_PREFIX: str = "/api"
    MT5_SESSION_KEEPALIVE_SECONDS: int = 120
    MT5_REQUEST_TIMEOUT_SECONDS: int = 30
    MT5_VERIFY_SSL: bool = True

    @property
    def mt5_configured(self) -> bool:
        return all([self.MT5_SERVER_URL, self.MT5_MANAGER_LOGIN, self.MT5_MANAGER_PASSWORD])

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
