import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api import auth, campaigns, bonuses, accounts, reports, audit, triggers, monitoring
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.gateway import gateway
    if hasattr(gateway, "connect"):
        try:
            await gateway.connect()
        except Exception:
            logger.exception("Failed to connect MT5 gateway at startup")
    start_scheduler()
    yield
    stop_scheduler()
    if hasattr(gateway, "disconnect"):
        await gateway.disconnect()


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
app.include_router(monitoring.router)


@app.get("/api/health")
async def health():
    from app.tasks.scheduler import scheduler
    from app.gateway import gateway
    monitor_job = scheduler.get_job("account_monitor")
    return {
        "status": "ok",
        "service": "mt5-bonus-plugin",
        "scheduler_running": scheduler.running,
        "gateway_mode": "real" if hasattr(gateway, "connect") else "mock",
        "monitor_active": monitor_job is not None,
    }


@app.get("/api/gateway/accounts")
async def list_gateway_accounts():
    from app.gateway import gateway
    if hasattr(gateway, "accounts"):
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
    return {"message": "Account listing not available in real MT5 mode. Use /api/accounts/{login} instead."}
