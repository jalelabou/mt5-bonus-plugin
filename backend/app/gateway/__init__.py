import logging

from app.config.settings import settings
from app.gateway.interface import MT5Gateway, MT5Account, MT5Deal  # noqa: F401

logger = logging.getLogger(__name__)


def _create_gateway() -> MT5Gateway:
    if settings.mt5_configured:
        from app.gateway.real import RealMT5Gateway
        logger.info(
            "Using REAL MT5 gateway -> bridge=%s server=%s manager=%s",
            settings.MT5_BRIDGE_URL,
            settings.MT5_SERVER,
            settings.MT5_MANAGER_LOGIN,
        )
        return RealMT5Gateway(
            bridge_url=settings.MT5_BRIDGE_URL,
            mt5_server=settings.MT5_SERVER,
            manager_login=settings.MT5_MANAGER_LOGIN,
            manager_password=settings.MT5_MANAGER_PASSWORD,
            request_timeout=settings.MT5_REQUEST_TIMEOUT_SECONDS,
        )
    else:
        from app.gateway.mock import MockMT5Gateway
        logger.info("Using MOCK MT5 gateway (no MT5_BRIDGE_URL configured)")
        return MockMT5Gateway()


gateway: MT5Gateway = _create_gateway()
