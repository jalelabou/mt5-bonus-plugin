from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./mt5_bonus.db"
    SECRET_KEY: str = "dev-secret-key-not-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # MT5 Manager REST API Bridge (leave blank for mock gateway)
    MT5_BRIDGE_URL: Optional[str] = None          # e.g. http://135.181.217.184:5000
    MT5_SERVER: Optional[str] = None              # MT5 server IP e.g. 173.234.17.76
    MT5_MANAGER_LOGIN: Optional[str] = None       # Manager login number
    MT5_MANAGER_PASSWORD: Optional[str] = None    # Manager password
    MT5_REQUEST_TIMEOUT_SECONDS: int = 30

    @property
    def mt5_configured(self) -> bool:
        return all([self.MT5_BRIDGE_URL, self.MT5_SERVER, self.MT5_MANAGER_LOGIN, self.MT5_MANAGER_PASSWORD])

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
