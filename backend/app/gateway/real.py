import logging
from typing import List, Optional

import httpx

from app.gateway.interface import MT5Account, MT5Deal, MT5Gateway

logger = logging.getLogger(__name__)


class MT5ManagerAPIError(Exception):
    def __init__(self, message: str, code: str = "", status_code: int = 0):
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class RealMT5Gateway(MT5Gateway):
    """Connects to MT5 via the Manager REST API bridge (mtapi-style)."""

    def __init__(
        self,
        bridge_url: str,
        mt5_server: str,
        manager_login: str,
        manager_password: str,
        request_timeout: int = 30,
    ):
        self._bridge_url = bridge_url.rstrip("/")
        self._mt5_server = mt5_server
        self._manager_login = manager_login
        self._manager_password = manager_password
        self._request_timeout = request_timeout
        self._token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    # -- Lifecycle --

    async def connect(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._request_timeout))
        resp = await self._client.get(f"{self._bridge_url}/Connect", params={
            "user": self._manager_login,
            "password": self._manager_password,
            "server": self._mt5_server,
        })
        if resp.status_code == 201 or resp.status_code >= 400:
            raise MT5ManagerAPIError(f"Connect failed: {resp.text}", status_code=resp.status_code)
        self._token = resp.text.strip().strip('"')
        logger.info("MT5 gateway connected (token=%s...)", self._token[:8])

    async def disconnect(self) -> None:
        if self._token and self._client:
            try:
                await self._client.get(f"{self._bridge_url}/Disconnect", params={"id": self._token})
            except Exception:
                pass
        if self._client:
            await self._client.aclose()
        logger.info("MT5 gateway disconnected")

    # -- Helpers --

    async def _ensure_connected(self) -> None:
        if not self._token:
            await self.connect()

    async def _get(self, path: str, **params) -> httpx.Response:
        await self._ensure_connected()
        params["id"] = self._token
        resp = await self._client.get(f"{self._bridge_url}{path}", params=params)
        # Check for error responses (status 201 = exception in this API)
        if resp.status_code == 201:
            try:
                err = resp.json()
                code = err.get("code", "")
                msg = err.get("message", resp.text)
                raise MT5ManagerAPIError(msg, code=code, status_code=201)
            except (ValueError, KeyError):
                raise MT5ManagerAPIError(resp.text, status_code=201)
        return resp

    # -- Interface methods --

    async def get_account_info(self, login: str) -> Optional[MT5Account]:
        try:
            # UserDetails has name, group, country, leverage
            user_resp = await self._get("/UserDetails", login=int(login))
            user = user_resp.json()

            # AccountDetails has balance, equity, credit
            acct_resp = await self._get("/AccountDetails", login=int(login))
            acct = acct_resp.json()

            return MT5Account(
                login=str(user.get("login", login)),
                balance=float(acct.get("balance", 0)),
                equity=float(acct.get("equity", 0)),
                credit=float(acct.get("credit", 0)),
                leverage=int(user.get("leverage", 0)),
                group=str(user.get("group", "")),
                country=str(user.get("country", "")),
                name=str(user.get("name", "")),
            )
        except MT5ManagerAPIError as e:
            if "NOTFOUND" in e.code or "NOTFOUND" in str(e):
                return None
            raise

    async def post_credit(self, login: str, amount: float, comment: str) -> bool:
        try:
            resp = await self._get("/Deposit",
                login=int(login), amount=amount, comment=comment, credit=True)
            logger.info("MT5 credit posted: login=%s amount=%.2f ticket=%s", login, amount, resp.text.strip())
            return True
        except MT5ManagerAPIError:
            logger.exception("MT5 post_credit failed: login=%s", login)
            return False

    async def remove_credit(self, login: str, amount: float, comment: str) -> bool:
        try:
            resp = await self._get("/Deposit",
                login=int(login), amount=-abs(amount), comment=comment, credit=True)
            logger.info("MT5 credit removed: login=%s amount=%.2f ticket=%s", login, amount, resp.text.strip())
            return True
        except MT5ManagerAPIError:
            logger.exception("MT5 remove_credit failed: login=%s", login)
            return False

    async def set_leverage(self, login: str, leverage: int) -> bool:
        try:
            resp = await self._get("/UserUpdate", Login=int(login), Leverage=leverage)
            logger.info("MT5 leverage set: login=%s leverage=%d", login, leverage)
            return True
        except MT5ManagerAPIError:
            logger.exception("MT5 set_leverage failed: login=%s", login)
            return False

    async def deposit_to_balance(self, login: str, amount: float, comment: str) -> bool:
        try:
            resp = await self._get("/Deposit",
                login=int(login), amount=amount, comment=comment, credit=False)
            logger.info("MT5 balance deposit: login=%s amount=%.2f ticket=%s", login, amount, resp.text.strip())
            return True
        except MT5ManagerAPIError:
            logger.exception("MT5 deposit_to_balance failed: login=%s", login)
            return False

    async def get_trade_history(
        self, login: str, from_timestamp: Optional[float] = None
    ) -> List[MT5Deal]:
        from datetime import datetime, timezone, timedelta
        try:
            if from_timestamp:
                dt_from = datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
            else:
                dt_from = datetime.now(timezone.utc) - timedelta(days=30)
            dt_to = datetime.now(timezone.utc)

            resp = await self._get("/DealHistory",
                login=int(login),
                **{"from": dt_from.strftime("%Y-%m-%dT%H:%M:%S"),
                   "to": dt_to.strftime("%Y-%m-%dT%H:%M:%S")})
            data = resp.json()
            if not isinstance(data, list):
                return []

            deals = []
            for d in data:
                # Skip balance/credit operations, only include trades
                action = d.get("action", "")
                if "DEAL_BUY" not in str(action) and "DEAL_SELL" not in str(action):
                    continue
                deals.append(MT5Deal(
                    deal_id=str(d.get("deal", d.get("ticket", ""))),
                    login=str(d.get("login", login)),
                    symbol=str(d.get("symbol", "")),
                    volume_lots=float(d.get("volume", 0)) / 10000.0 if d.get("volume", 0) > 100 else float(d.get("volume", 0)),
                    price=float(d.get("price", 0)),
                    profit=float(d.get("profit", 0)),
                    timestamp=float(d.get("time", 0)),
                    entry="in" if d.get("entry", "") == "ENTRY_IN" else "out",
                ))
            return deals
        except MT5ManagerAPIError:
            logger.exception("MT5 get_trade_history failed: login=%s", login)
            return []

    async def get_account_group(self, login: str) -> Optional[str]:
        account = await self.get_account_info(login)
        return account.group if account else None
