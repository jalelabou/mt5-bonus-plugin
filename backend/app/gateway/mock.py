import time
import random
from typing import Dict, List, Optional

from app.gateway.interface import MT5Account, MT5BalanceDeal, MT5Deal, MT5Gateway


class MockMT5Gateway(MT5Gateway):
    def __init__(self):
        self.accounts: Dict[str, MT5Account] = {}
        self.deals: Dict[str, List[MT5Deal]] = {}
        self._balance_deals: Dict[str, List[MT5BalanceDeal]] = {}
        self._deal_counter = 1000
        self._seed_accounts()

    def _seed_accounts(self):
        test_accounts = [
            ("10001", 5000.0, 500, "demo\\standard", "US", "John Doe", "IB001"),
            ("10002", 10000.0, 200, "demo\\standard", "UK", "Jane Smith", "IB002"),
            ("10003", 2500.0, 1000, "demo\\premium", "DE", "Hans Mueller", ""),
            ("10004", 50000.0, 100, "live\\standard", "JP", "Taro Yamada", "IB003"),
            ("10005", 1000.0, 500, "demo\\standard", "AU", "Alice Brown", ""),
            ("10006", 7500.0, 300, "live\\premium", "CA", "Bob Wilson", "IB001"),
            ("10007", 15000.0, 200, "demo\\vip", "FR", "Pierre Dupont", ""),
            ("10008", 3000.0, 500, "live\\standard", "BR", "Carlos Silva", "IB002"),
            ("10009", 20000.0, 100, "live\\vip", "SG", "Wei Chen", ""),
            ("10010", 500.0, 500, "demo\\micro", "IN", "Raj Patel", ""),
        ]
        for login, balance, leverage, group, country, name, lead_source in test_accounts:
            self.accounts[login] = MT5Account(
                login=login,
                balance=balance,
                equity=balance,
                credit=0.0,
                leverage=leverage,
                group=group,
                country=country,
                name=name,
                lead_source=lead_source,
            )
            self.deals[login] = []

    async def get_account_info(self, login: str) -> Optional[MT5Account]:
        return self.accounts.get(login)

    async def post_credit(self, login: str, amount: float, comment: str) -> bool:
        acct = self.accounts.get(login)
        if not acct:
            return False
        acct.credit += amount
        acct.equity += amount
        return True

    async def remove_credit(self, login: str, amount: float, comment: str) -> bool:
        acct = self.accounts.get(login)
        if not acct:
            return False
        acct.credit = max(0, acct.credit - amount)
        acct.equity = acct.balance + acct.credit
        return True

    async def set_leverage(self, login: str, leverage: int) -> bool:
        acct = self.accounts.get(login)
        if not acct:
            return False
        acct.leverage = leverage
        return True

    async def deposit_to_balance(self, login: str, amount: float, comment: str) -> bool:
        acct = self.accounts.get(login)
        if not acct:
            return False
        acct.balance += amount
        acct.credit = max(0, acct.credit - amount)
        acct.equity = acct.balance + acct.credit
        return True

    async def get_trade_history(
        self, login: str, from_timestamp: Optional[float] = None
    ) -> List[MT5Deal]:
        deals = self.deals.get(login, [])
        if from_timestamp:
            deals = [d for d in deals if d.timestamp >= from_timestamp]
        return deals

    async def close_all_positions(self, login: str) -> bool:
        return True

    async def get_all_logins(self) -> List[str]:
        return list(self.accounts.keys())

    async def get_all_groups(self) -> List[str]:
        return list({a.group for a in self.accounts.values()})

    async def get_account_group(self, login: str) -> Optional[str]:
        acct = self.accounts.get(login)
        return acct.group if acct else None

    async def get_balance_deals(
        self, login: str, from_timestamp: Optional[float] = None
    ) -> List[MT5BalanceDeal]:
        deals = self._balance_deals.get(login, [])
        if from_timestamp:
            deals = [d for d in deals if d.timestamp >= from_timestamp]
        return deals

    def simulate_deposit(self, login: str, amount: float) -> MT5BalanceDeal:
        self._deal_counter += 1
        deal = MT5BalanceDeal(
            deal_id=str(self._deal_counter),
            login=login,
            amount=amount,
            timestamp=time.time(),
            comment="Deposit",
        )
        self._balance_deals.setdefault(login, []).append(deal)
        acct = self.accounts.get(login)
        if acct:
            acct.balance += amount
            acct.equity += amount
        return deal

    def simulate_deal(self, login: str, symbol: str = "EURUSD", lots: float = 1.0) -> MT5Deal:
        self._deal_counter += 1
        deal = MT5Deal(
            deal_id=str(self._deal_counter),
            login=login,
            symbol=symbol,
            volume_lots=lots,
            price=round(1.0 + random.random() * 0.5, 5),
            profit=round(random.uniform(-100, 200), 2),
            timestamp=time.time(),
            entry="out",
        )
        if login not in self.deals:
            self.deals[login] = []
        self.deals[login].append(deal)
        return deal


# Singleton
gateway = MockMT5Gateway()
