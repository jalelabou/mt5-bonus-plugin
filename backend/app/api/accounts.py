from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.gateway.mock import gateway
from app.models.audit_log import AuditLog
from app.models.bonus import Bonus
from app.models.campaign import Campaign
from app.models.user import AdminUser
from app.schemas.audit_log import AuditLogRead
from app.schemas.bonus import BonusRead

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/{login}")
async def account_lookup(
    login: str,
    db: AsyncSession = Depends(get_db),
    user: AdminUser = Depends(get_current_user),
):
    account = await gateway.get_account_info(login)
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")

    # Get bonuses
    result = await db.execute(
        select(Bonus, Campaign.name)
        .join(Campaign, Bonus.campaign_id == Campaign.id)
        .where(Bonus.mt5_login == login)
        .order_by(Bonus.assigned_at.desc())
    )
    bonus_rows = result.all()
    bonuses = []
    for bonus, campaign_name in bonus_rows:
        item = BonusRead.model_validate(bonus)
        item.campaign_name = campaign_name
        if bonus.bonus_type == "C" and bonus.lots_required:
            item.percent_converted = round(bonus.lots_traded / bonus.lots_required * 100, 2)
        bonuses.append(item)

    # Get audit logs
    audit_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.mt5_login == login)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    audit_logs = [AuditLogRead.model_validate(a) for a in audit_result.scalars().all()]

    return {
        "account": {
            "login": account.login,
            "name": account.name,
            "balance": account.balance,
            "equity": account.equity,
            "credit": account.credit,
            "leverage": account.leverage,
            "group": account.group,
            "country": account.country,
        },
        "bonuses": bonuses,
        "audit_logs": audit_logs,
    }
