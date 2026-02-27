from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MT5Account:
    login: str
    balance: float
    equity: float
    credit: float
    leverage: int
    group: str
    country: str
    name: str


@dataclass
class MT5Deal:
    deal_id: str
    login: str
    symbol: str
    volume_lots: float
    price: float
    profit: float
    timestamp: float
    entry: str  # "in" or "out"


class MT5Gateway(ABC):
    @abstractmethod
    async def get_account_info(self, login: str) -> Optional[MT5Account]:
        pass

    @abstractmethod
    async def post_credit(self, login: str, amount: float, comment: str) -> bool:
        pass

    @abstractmethod
    async def remove_credit(self, login: str, amount: float, comment: str) -> bool:
        pass

    @abstractmethod
    async def set_leverage(self, login: str, leverage: int) -> bool:
        pass

    @abstractmethod
    async def deposit_to_balance(self, login: str, amount: float, comment: str) -> bool:
        pass

    @abstractmethod
    async def get_trade_history(
        self, login: str, from_timestamp: Optional[float] = None
    ) -> List[MT5Deal]:
        pass

    @abstractmethod
    async def get_account_group(self, login: str) -> Optional[str]:
        pass
