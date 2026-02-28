from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus, TriggerType
from app.models.trigger import TriggerEvent, TriggerStatus
from app.services.bonus_engine import assign_bonus, check_eligibility


async def process_deposit_trigger(
    db: AsyncSession,
    mt5_login: str,
    deposit_amount: float,
    agent_code: Optional[str] = None,
) -> List[dict]:
    results = []

    # Collect all matching campaigns: auto_deposit + agent_code (via lead source)
    seen_ids: set[int] = set()
    campaigns: List[Campaign] = []

    for c in await _get_active_campaigns_for_trigger("auto_deposit", db):
        if c.id in seen_ids:
            continue
        # If this campaign also has agent_codes configured, it requires a matching
        # lead source — skip it if the account has no lead source or doesn't match.
        if c.agent_codes:
            if not agent_code or agent_code not in c.agent_codes:
                continue
        seen_ids.add(c.id)
        campaigns.append(c)

    if agent_code:
        for c in await _get_active_campaigns_for_trigger("agent_code", db):
            if c.id not in seen_ids and c.agent_codes and agent_code in c.agent_codes:
                seen_ids.add(c.id)
                campaigns.append(c)

    for campaign in campaigns:
        eligible, reason = await check_eligibility(db, campaign, mt5_login, deposit_amount)

        trigger_event = TriggerEvent(
            campaign_id=campaign.id,
            mt5_login=mt5_login,
            trigger_type="agent_code" if (agent_code and campaign.agent_codes and agent_code in campaign.agent_codes) else "auto_deposit",
            event_data={"deposit_amount": deposit_amount, "agent_code": agent_code},
        )

        if eligible:
            try:
                bonus = await assign_bonus(db, campaign, mt5_login, deposit_amount)
                trigger_event.status = TriggerStatus.PROCESSED
                trigger_event.processed_at = datetime.now(timezone.utc)
                results.append({"campaign_id": campaign.id, "bonus_id": bonus.id, "status": "assigned"})
            except Exception as e:
                trigger_event.status = TriggerStatus.FAILED
                trigger_event.skip_reason = str(e)
                results.append({"campaign_id": campaign.id, "status": "failed", "error": str(e)})
        else:
            trigger_event.status = TriggerStatus.SKIPPED
            trigger_event.skip_reason = reason
            results.append({"campaign_id": campaign.id, "status": "skipped", "reason": reason})

        db.add(trigger_event)

    await db.flush()
    return results


async def process_registration_trigger(
    db: AsyncSession,
    mt5_login: str,
) -> List[dict]:
    results = []
    campaigns = await _get_active_campaigns_for_trigger("registration", db)

    for campaign in campaigns:
        eligible, reason = await check_eligibility(db, campaign, mt5_login)

        trigger_event = TriggerEvent(
            campaign_id=campaign.id,
            mt5_login=mt5_login,
            trigger_type="registration",
            event_data={},
        )

        if eligible:
            try:
                bonus = await assign_bonus(db, campaign, mt5_login, deposit_amount=0)
                trigger_event.status = TriggerStatus.PROCESSED
                trigger_event.processed_at = datetime.now(timezone.utc)
                results.append({"campaign_id": campaign.id, "bonus_id": bonus.id, "status": "assigned"})
            except Exception as e:
                trigger_event.status = TriggerStatus.FAILED
                trigger_event.skip_reason = str(e)
                results.append({"campaign_id": campaign.id, "status": "failed", "error": str(e)})
        else:
            trigger_event.status = TriggerStatus.SKIPPED
            trigger_event.skip_reason = reason
            results.append({"campaign_id": campaign.id, "status": "skipped", "reason": reason})

        db.add(trigger_event)

    await db.flush()
    return results


async def process_promo_code_trigger(
    db: AsyncSession,
    mt5_login: str,
    promo_code: str,
    deposit_amount: Optional[float] = None,
) -> List[dict]:
    results = []
    query = select(Campaign).where(
        Campaign.status == CampaignStatus.ACTIVE,
        Campaign.promo_code == promo_code,
    )
    result = await db.execute(query)
    campaigns = result.scalars().all()

    for campaign in campaigns:
        eligible, reason = await check_eligibility(db, campaign, mt5_login, deposit_amount)

        trigger_event = TriggerEvent(
            campaign_id=campaign.id,
            mt5_login=mt5_login,
            trigger_type="promo_code",
            event_data={"promo_code": promo_code, "deposit_amount": deposit_amount},
        )

        if eligible:
            try:
                bonus = await assign_bonus(db, campaign, mt5_login, deposit_amount)
                trigger_event.status = TriggerStatus.PROCESSED
                trigger_event.processed_at = datetime.now(timezone.utc)
                results.append({"campaign_id": campaign.id, "bonus_id": bonus.id, "status": "assigned"})
            except Exception as e:
                trigger_event.status = TriggerStatus.FAILED
                trigger_event.skip_reason = str(e)
                results.append({"campaign_id": campaign.id, "status": "failed", "error": str(e)})
        else:
            trigger_event.status = TriggerStatus.SKIPPED
            trigger_event.skip_reason = reason
            results.append({"campaign_id": campaign.id, "status": "skipped", "reason": reason})

        db.add(trigger_event)

    await db.flush()
    return results


async def _get_active_campaigns_for_trigger(
    trigger_type: str, db: AsyncSession
) -> List[Campaign]:
    query = select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
    result = await db.execute(query)
    all_active = result.scalars().all()
    return [c for c in all_active if trigger_type in (c.trigger_types or [])]
