from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.interface import MT5Deal
from app.models.bonus import Bonus, BonusStatus
from app.services.lot_tracker import handle_withdrawal, process_deal


async def process_deal_event(db: AsyncSession, deal: MT5Deal):
    result = await db.execute(
        select(Bonus).where(
            Bonus.mt5_login == deal.login,
            Bonus.status == BonusStatus.ACTIVE,
            Bonus.bonus_type == "C",
        )
    )
    bonuses = result.scalars().all()

    for bonus in bonuses:
        await process_deal(db, bonus, deal)


async def process_withdrawal_event(db: AsyncSession, mt5_login: str, amount: float):
    from app.services.monitor_service import _proportional_reduce_bonuses, _get_active_bonuses
    from app.gateway import gateway

    # Calculate withdrawal ratio from current MT5 balance
    account = await gateway.get_account_info(mt5_login)
    if account:
        balance_before = account.balance + amount  # reconstruct pre-withdrawal balance
        withdrawal_ratio = amount / balance_before if balance_before > 0 else 1.0
    else:
        withdrawal_ratio = 1.0

    if withdrawal_ratio >= 1.0:
        # Full withdrawal — cancel everything
        from app.services.bonus_engine import cancel_bonus
        result = await db.execute(
            select(Bonus).where(
                Bonus.mt5_login == mt5_login,
                Bonus.status == BonusStatus.ACTIVE,
            )
        )
        bonuses = result.scalars().all()
        for bonus in bonuses:
            if bonus.bonus_type == "C":
                await handle_withdrawal(db, bonus, amount)
            else:
                await cancel_bonus(db, bonus, reason=f"withdrawal:{amount:.2f}")
    else:
        # Partial withdrawal — proportional reduction
        await _proportional_reduce_bonuses(db, mt5_login, withdrawal_ratio, amount)
