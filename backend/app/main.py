import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api import auth, campaigns, bonuses, accounts, reports, audit, triggers
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="MT5 Bonus Plugin",
    description="Broker-side bonus campaign management for MetaTrader 5",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(bonuses.router)
app.include_router(accounts.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(triggers.router)


@app.get("/api/health")
async def health():
    from app.tasks.scheduler import scheduler
    return {
        "status": "ok",
        "service": "mt5-bonus-plugin",
        "scheduler_running": scheduler.running,
    }


@app.get("/api/gateway/accounts")
async def list_mock_accounts():
    from app.gateway.mock import gateway
    return {
        login: {
            "login": acct.login,
            "name": acct.name,
            "balance": acct.balance,
            "equity": acct.equity,
            "credit": acct.credit,
            "leverage": acct.leverage,
            "group": acct.group,
            "country": acct.country,
        }
        for login, acct in gateway.accounts.items()
    }
