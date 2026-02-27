import asyncio
import logging
import time
from typing import List, Optional

import httpx

from app.gateway.interface import MT5Account, MT5Deal, MT5Gateway

logger = logging.getLogger(__name__)


class MT5WebAPIError(Exception):
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class RealMT5Gateway(MT5Gateway):
    def __init__(
        self,
        server_url: str,
        manager_login: str,
        manager_password: str,
        api_prefix: str = "/api",
        keepalive_seconds: int = 120,
        request_timeout: int = 30,
        verify_ssl: bool = True,
    ):
        self._server_url = server_url.rstrip("/")
        self._manager_login = manager_login
        self._manager_password = manager_password
        self._api_prefix = api_prefix
        self._keepalive_seconds = keepalive_seconds
        self._request_timeout = request_timeout
        self._verify_ssl = verify_ssl

        self._base_url = f"{self._server_url}{self._api_prefix}"
        self._auth_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    # -- Lifecycle --

    async def connect(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._request_timeout),
            verify=self._verify_ssl,
        )
        await self._authenticate()
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        logger.info("MT5 gateway connected to %s", self._server_url)

    async def disconnect(self) -> None:
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
        logger.info("MT5 gateway disconnected")

    # -- Authentication --

    async def _authenticate(self) -> None:
        url = f"{self._base_url}/auth/start"
        payload = {
            "login": self._manager_login,
            "password": self._manager_password,
        }
        logger.debug("MT5 authenticating as manager %s", self._manager_login)
        resp = await self._client.post(url, json=payload)
        if resp.status_code != 200:
            raise MT5WebAPIError(
                f"MT5 auth failed: {resp.status_code}",
                status_code=resp.status_code,
                response_body=resp.text,
            )
        data = resp.json()
        self._auth_token = data.get("token") or data.get("session") or data.get("access_token")
        if not self._auth_token:
            raise MT5WebAPIError("MT5 auth response missing token field", response_body=resp.text)
        logger.info("MT5 authenticated successfully")

    async def _ensure_authenticated(self) -> None:
        async with self._lock:
            if not self._auth_token:
                await self._authenticate()

    async def _keepalive_loop(self) -> None:
        while True:
            await asyncio.sleep(self._keepalive_seconds)
            try:
                await self._request("GET", "/auth/keepalive")
            except Exception:
                logger.warning("MT5 keepalive failed, re-authenticating")
                try:
                    await self._authenticate()
                except Exception:
                    logger.exception("MT5 re-authentication failed")

    # -- HTTP helper --

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        await self._ensure_authenticated()
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._auth_token}"}

        resp = await self._client.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            logger.warning("MT5 session expired, re-authenticating")
            async with self._lock:
                await self._authenticate()
            headers = {"Authorization": f"Bearer {self._auth_token}"}
            resp = await self._client.request(method, url, headers=headers, **kwargs)

        if resp.status_code >= 400:
            raise MT5WebAPIError(
                f"MT5 API {method} {path} failed: {resp.status_code}",
                status_code=resp.status_code,
                response_body=resp.text[:500],
            )

        return resp.json() if resp.text.strip() else {}

    # -- Interface methods --

    async def get_account_info(self, login: str) -> Optional[MT5Account]:
        try:
            data = await self._request("GET", "/user/get", params={"login": login})
            return MT5Account(
                login=str(data.get("Login", login)),
                balance=float(data.get("Balance", 0)),
                equity=float(data.get("Equity", 0)),
                credit=float(data.get("Credit", 0)),
                leverage=int(data.get("Leverage", 0)),
                group=str(data.get("Group", "")),
                country=str(data.get("Country", "")),
                name=str(data.get("Name", "")),
            )
        except MT5WebAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def post_credit(self, login: str, amount: float, comment: str) -> bool:
        try:
            await self._request("POST", "/trade/balance", json={
                "Login": int(login),
                "Type": 3,  # Credit in
                "Balance": amount,
                "Comment": comment,
            })
            logger.info("MT5 credit posted: login=%s amount=%.2f", login, amount)
            return True
        except MT5WebAPIError:
            logger.exception("MT5 post_credit failed: login=%s", login)
            return False

    async def remove_credit(self, login: str, amount: float, comment: str) -> bool:
        try:
            await self._request("POST", "/trade/balance", json={
                "Login": int(login),
                "Type": 4,  # Credit out
                "Balance": -abs(amount),
                "Comment": comment,
            })
            logger.info("MT5 credit removed: login=%s amount=%.2f", login, amount)
            return True
        except MT5WebAPIError:
            logger.exception("MT5 remove_credit failed: login=%s", login)
            return False

    async def set_leverage(self, login: str, leverage: int) -> bool:
        try:
            await self._request("POST", "/user/update", json={
                "Login": int(login),
                "Leverage": leverage,
            })
            logger.info("MT5 leverage set: login=%s leverage=%d", login, leverage)
            return True
        except MT5WebAPIError:
            logger.exception("MT5 set_leverage failed: login=%s", login)
            return False

    async def deposit_to_balance(self, login: str, amount: float, comment: str) -> bool:
        try:
            await self._request("POST", "/trade/balance", json={
                "Login": int(login),
                "Type": 2,  # Balance deposit
                "Balance": amount,
                "Comment": comment,
            })
            logger.info("MT5 balance deposit: login=%s amount=%.2f", login, amount)
            return True
        except MT5WebAPIError:
            logger.exception("MT5 deposit_to_balance failed: login=%s", login)
            return False

    async def get_trade_history(
        self, login: str, from_timestamp: Optional[float] = None
    ) -> List[MT5Deal]:
        params: dict = {"login": login, "to": str(int(time.time()))}
        if from_timestamp:
            params["from"] = str(int(from_timestamp))

        try:
            data = await self._request("GET", "/deal/get_page", params=params)
            raw_deals = data.get("deals", data if isinstance(data, list) else [])
            deals = []
            for d in raw_deals:
                deals.append(MT5Deal(
                    deal_id=str(d.get("Deal", "")),
                    login=str(d.get("Login", login)),
                    symbol=str(d.get("Symbol", "")),
                    volume_lots=float(d.get("Volume", 0)) / 10000.0,
                    price=float(d.get("Price", 0)),
                    profit=float(d.get("Profit", 0)),
                    timestamp=float(d.get("Time", 0)),
                    entry="in" if d.get("Entry", 0) == 0 else "out",
                ))
            return deals
        except MT5WebAPIError:
            logger.exception("MT5 get_trade_history failed: login=%s", login)
            return []

    async def get_account_group(self, login: str) -> Optional[str]:
        account = await self.get_account_info(login)
        return account.group if account else None
