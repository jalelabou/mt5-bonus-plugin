import math

from app.gateway.interface import MT5Gateway


def calculate_adjusted_leverage(original_leverage: int, bonus_percentage: float) -> int:
    multiplier = (bonus_percentage / 100.0) + 1.0
    return math.floor(original_leverage / multiplier)


async def apply_leverage_reduction(
    gateway: MT5Gateway, login: str, original_leverage: int, bonus_percentage: float
) -> int:
    adjusted = calculate_adjusted_leverage(original_leverage, bonus_percentage)
    await gateway.set_leverage(login, adjusted)
    return adjusted


async def restore_leverage(gateway: MT5Gateway, login: str, original_leverage: int) -> bool:
    return await gateway.set_leverage(login, original_leverage)
