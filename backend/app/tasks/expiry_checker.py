from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bonus import Bonus, BonusStatus
from app.services.bonus_engine import expire_bonus


async def check_expired_bonuses(db: AsyncSession):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Bonus).where(
            Bonus.status == BonusStatus.ACTIVE,
            Bonus.expires_at.isnot(None),
            Bonus.expires_at <= now,
        )
    )
    expired = result.scalars().all()

    count = 0
    for bonus in expired:
        await expire_bonus(db, bonus)
        count += 1

    return count
