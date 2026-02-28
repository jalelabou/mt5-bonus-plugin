import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway import gateway
from app.models.bonus import Bonus, BonusStatus
from app.models.monitored_account import MonitoredAccount
from app.services.bonus_engine import cancel_bonus
from app.services.trigger_service import process_deposit_trigger
from app.tasks.event_processor import process_deal_event

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_ERRORS = 5


async def register_for_monitoring(
    db: AsyncSession, mt5_login: str, reason: str = "active_bonus"
) -> MonitoredAccount:
    """Add or update an account in the monitoring table."""
    result = await db.execute(
        select(MonitoredAccount).where(MonitoredAccount.mt5_login == mt5_login)
    )
    mon = result.scalar_one_or_none()

    if mon is None:
        # Fetch current snapshot from MT5
        account = await gateway.get_account_info(mt5_login)
        mon = MonitoredAccount(
            mt5_login=mt5_login,
            last_balance=account.balance if account else 0.0,
            last_equity=account.equity if account else 0.0,
            last_credit=account.credit if account else 0.0,
            last_deal_timestamp=0.0,  # Start from beginning to catch all deals
            is_active=True,
            monitor_reasons=[reason],
            last_polled_at=datetime.now(timezone.utc),
        )
        db.add(mon)
    else:
        # Refresh snapshot from MT5 to avoid stale data
        account = await gateway.get_account_info(mt5_login)
        if account:
            mon.last_balance = account.balance
            mon.last_equity = account.equity
            mon.last_credit = account.credit
        reasons = mon.monitor_reasons or []
        if reason not in reasons:
            mon.monitor_reasons = reasons + [reason]
        mon.is_active = True
        mon.consecutive_errors = 0

    await db.flush()
    return mon


async def unregister_if_no_bonuses(db: AsyncSession, mt5_login: str):
    """Deactivate monitoring if account has no active bonuses."""
    active_q = await db.execute(
        select(Bonus.id).where(
            Bonus.mt5_login == mt5_login,
            Bonus.status == BonusStatus.ACTIVE,
        )
    )
    if active_q.first() is not None:
        return  # Still has active bonuses

    result = await db.execute(
        select(MonitoredAccount).where(MonitoredAccount.mt5_login == mt5_login)
    )
    mon = result.scalar_one_or_none()
    if mon:
        # Keep monitoring if registered for deposit watching or auto-discovered
        keep_reasons = {"deposit_watch", "auto_discovered"}
        remaining = [r for r in (mon.monitor_reasons or []) if r in keep_reasons]
        if not remaining:
            mon.is_active = False
            mon.monitor_reasons = []
        else:
            mon.monitor_reasons = remaining
        await db.flush()


async def poll_single_account(db: AsyncSession, mon: MonitoredAccount) -> dict:
    """
    Poll one monitored account. Returns summary of actions taken.
    Order: deposits -> withdrawal/drawdown -> Type C trades -> update snapshot.
    """
    actions = {"login": mon.mt5_login, "deposits": 0, "withdrawals": 0,
               "drawdowns": 0, "deals": 0}

    try:
        account = await gateway.get_account_info(mon.mt5_login)
        if account is None:
            mon.consecutive_errors += 1
            mon.last_error = "Account not found in MT5"
            return actions

        # === DEPOSIT DETECTION ===
        # Balance increased and credit didn't increase (no bonus was just assigned)
        balance_delta = account.balance - mon.last_balance
        logger.debug(
            "Poll %s: bal=%.2f last=%.2f delta=%.2f credit=%.2f last_credit=%.2f",
            mon.mt5_login, account.balance, mon.last_balance, balance_delta,
            account.credit, mon.last_credit,
        )
        if balance_delta > 0.01 and account.credit <= mon.last_credit + 0.01:
            # Try to get individual deposits from deal history
            balance_deals = await gateway.get_balance_deals(
                mon.mt5_login, from_timestamp=mon.last_deal_timestamp
            )
            deposits_found = [d for d in balance_deals if d.amount > 0]

            if deposits_found:
                for deal in deposits_found:
                    logger.info(
                        "Auto-deposit detected: login=%s amount=%.2f deal=%s",
                        mon.mt5_login, deal.amount, deal.deal_id,
                    )
                    await process_deposit_trigger(db, mon.mt5_login, deal.amount)
                    actions["deposits"] += 1
                    if deal.timestamp > mon.last_deal_timestamp:
                        mon.last_deal_timestamp = deal.timestamp
            else:
                # Deal history didn't return details — use balance delta directly
                logger.info(
                    "Auto-deposit detected (via snapshot): login=%s amount=%.2f",
                    mon.mt5_login, balance_delta,
                )
                await process_deposit_trigger(db, mon.mt5_login, balance_delta)
                actions["deposits"] += 1

            # Re-fetch account after trigger may have posted credit
            account = await gateway.get_account_info(mon.mt5_login)
            if account is None:
                mon.consecutive_errors += 1
                return actions

        # === WITHDRAWAL DETECTION ===
        if account.balance < mon.last_balance - 0.01:
            withdrawal_amount = mon.last_balance - account.balance
            logger.info(
                "Withdrawal detected: login=%s amount=%.2f",
                mon.mt5_login, withdrawal_amount,
            )
            await _cancel_all_bonuses_and_clear_credit(
                db, mon.mt5_login,
                reason=f"withdrawal_detected:{withdrawal_amount:.2f}",
            )
            actions["withdrawals"] += 1
            # Re-fetch after credit removal
            account = await gateway.get_account_info(mon.mt5_login)
            if account is None:
                mon.consecutive_errors += 1
                return actions

        # === DRAWDOWN DETECTION ===
        # If equity <= credit, trader has lost all their own money.
        # E.g. $1000 deposit + $1000 credit = $2000 equity.
        # When equity drops to $1000 (credit), their $1000 is gone.
        if account.credit > 0 and account.equity <= account.credit + 0.01:
            own_equity = account.equity - account.credit
            reason = (
                f"Drawdown breach: trader equity depleted. "
                f"Equity={account.equity:.2f}, Credit={account.credit:.2f}, "
                f"Trader own funds={own_equity:.2f}. "
                f"All trades closed and bonus credit removed."
            )
            logger.warning(
                "Drawdown breach: login=%s equity=%.2f <= credit=%.2f — "
                "closing all trades and removing credit",
                mon.mt5_login, account.equity, account.credit,
            )
            # Close positions and cancel bonuses + remove credit
            await _close_positions_and_clear_credit(
                db, mon.mt5_login, reason=reason,
            )
            actions["drawdowns"] += 1
            # Re-fetch after credit removal
            account = await gateway.get_account_info(mon.mt5_login)
            if account is None:
                mon.consecutive_errors += 1
                return actions

        # === ORPHANED CREDIT CLEANUP ===
        # If MT5 still has credit but no active bonuses in DB, keep trying to remove it.
        # This catches cases where previous credit removal failed (e.g. positions were open).
        if account.credit > 0.01:
            active_bonuses = await _get_active_bonuses(db, mon.mt5_login)
            if not active_bonuses:
                logger.info(
                    "Orphaned credit cleanup: login=%s credit=%.2f (no active bonuses)",
                    mon.mt5_login, account.credit,
                )
                await _force_remove_credit(mon.mt5_login)
                account = await gateway.get_account_info(mon.mt5_login)
                if account is None:
                    mon.consecutive_errors += 1
                    return actions

        # === TYPE C TRADE TRACKING ===
        type_c_bonuses = await _get_active_type_c_bonuses(db, mon.mt5_login)
        if type_c_bonuses:
            trades = await gateway.get_trade_history(
                mon.mt5_login, from_timestamp=mon.last_deal_timestamp
            )
            for deal in trades:
                await process_deal_event(db, deal)
                actions["deals"] += 1
                if deal.timestamp > mon.last_deal_timestamp:
                    mon.last_deal_timestamp = deal.timestamp

        # === UPDATE SNAPSHOT ===
        # Use the already-fetched `account` (which may have been re-fetched after
        # deposit/withdrawal/drawdown handling). Do NOT make a new API call here,
        # as balance could change between the initial check and now, silently
        # missing a deposit.
        mon.last_balance = account.balance
        mon.last_equity = account.equity
        mon.last_credit = account.credit

        mon.last_polled_at = datetime.now(timezone.utc)
        mon.consecutive_errors = 0
        mon.last_error = None

    except Exception as e:
        mon.consecutive_errors += 1
        mon.last_error = str(e)[:500]
        logger.exception("Monitor poll failed: login=%s", mon.mt5_login)

    await db.flush()
    return actions


async def run_monitor_cycle(db: AsyncSession) -> dict:
    """Main entry point called by the scheduler. Polls all active monitored accounts."""
    # Auto-discover new MT5 accounts and register them
    try:
        all_logins = await gateway.get_all_logins()
        if all_logins:
            existing = await db.execute(select(MonitoredAccount))
            existing_map = {m.mt5_login: m for m in existing.scalars().all()}
            for login in all_logins:
                login_str = str(login)
                if login_str not in existing_map:
                    await register_for_monitoring(db, login_str, reason="auto_discovered")
                    logger.info("Auto-discovered new MT5 account: %s", login_str)
                elif not existing_map[login_str].is_active:
                    # Reactivate inactive accounts found on MT5
                    mon = existing_map[login_str]
                    mon.is_active = True
                    if "auto_discovered" not in (mon.monitor_reasons or []):
                        mon.monitor_reasons = (mon.monitor_reasons or []) + ["auto_discovered"]
                    logger.info("Reactivated MT5 account: %s", login_str)
            await db.flush()
    except Exception:
        logger.exception("Account auto-discovery failed")

    result = await db.execute(
        select(MonitoredAccount).where(
            MonitoredAccount.is_active == True,  # noqa: E712
            MonitoredAccount.consecutive_errors < MAX_CONSECUTIVE_ERRORS,
        ).order_by(MonitoredAccount.last_polled_at.asc().nullsfirst())
    )
    accounts = result.scalars().all()

    summary = {
        "total": len(accounts), "deposits": 0, "withdrawals": 0,
        "drawdowns": 0, "deals": 0, "errors": 0,
    }

    for mon in accounts:
        poll_result = await poll_single_account(db, mon)
        summary["deposits"] += poll_result["deposits"]
        summary["withdrawals"] += poll_result["withdrawals"]
        summary["drawdowns"] += poll_result["drawdowns"]
        summary["deals"] += poll_result["deals"]
        if mon.consecutive_errors > 0:
            summary["errors"] += 1

    return summary


async def _close_positions_and_clear_credit(
    db: AsyncSession, mt5_login: str, reason: str
):
    """Close all positions, cancel all bonuses, then remove credit with verification."""
    import asyncio as _asyncio

    # Step 1: Close all open positions (try multiple times)
    for attempt in range(3):
        await gateway.close_all_positions(mt5_login)
        await _asyncio.sleep(1.5)
        # Check if positions are actually closed (equity should be ~balance+credit)
        acct = await gateway.get_account_info(mt5_login)
        if acct and abs(acct.equity - acct.balance - acct.credit) < 1.0:
            logger.info("Positions closed for %s (attempt %d)", mt5_login, attempt + 1)
            break
        logger.warning(
            "Positions may still be open for %s: equity=%.2f, balance+credit=%.2f (attempt %d)",
            mt5_login, acct.equity if acct else 0, (acct.balance + acct.credit) if acct else 0, attempt + 1,
        )

    # Step 2: Cancel all bonuses in DB
    await _cancel_all_bonuses_in_db(db, mt5_login, reason)

    # Step 3: Remove credit with verification
    await _force_remove_credit(mt5_login)

    # Unregister from monitoring if no bonuses left
    await unregister_if_no_bonuses(db, mt5_login)


async def _cancel_all_bonuses_and_clear_credit(
    db: AsyncSession, mt5_login: str, reason: str
):
    """Cancel all active bonuses, then wipe any remaining credit from MT5."""
    await _cancel_all_bonuses_in_db(db, mt5_login, reason)
    await _force_remove_credit(mt5_login)
    await unregister_if_no_bonuses(db, mt5_login)


async def _cancel_all_bonuses_in_db(
    db: AsyncSession, mt5_login: str, reason: str
):
    """Mark all active bonuses as cancelled in the DB."""
    active_bonuses = await _get_active_bonuses(db, mt5_login)

    now = datetime.now(timezone.utc)
    for bonus in active_bonuses:
        if bonus.bonus_type == "A" and bonus.original_leverage:
            from app.services.leverage_service import restore_leverage
            await restore_leverage(gateway, bonus.mt5_login, bonus.original_leverage)

        bonus.status = BonusStatus.CANCELLED
        bonus.cancelled_at = now
        bonus.cancellation_reason = reason

        from app.models.audit_log import ActorType, EventType
        from app.services.audit_service import log_event
        await log_event(
            db,
            event_type=EventType.CANCELLATION,
            mt5_login=bonus.mt5_login,
            campaign_id=bonus.campaign_id,
            bonus_id=bonus.id,
            actor_type=ActorType.SYSTEM,
            before_state={"status": "active", "bonus_amount": bonus.bonus_amount},
            after_state={"status": "cancelled", "reason": reason},
        )

    await db.flush()


async def _force_remove_credit(mt5_login: str):
    """Remove all credit from MT5 account, retrying and verifying after each attempt."""
    import asyncio as _asyncio

    for attempt in range(5):
        account = await gateway.get_account_info(mt5_login)
        if not account or account.credit <= 0.01:
            logger.info("Credit cleared for %s (credit=%.2f)", mt5_login, account.credit if account else 0)
            return

        # If positions are still open (equity != balance + credit), close them first
        if abs(account.equity - account.balance - account.credit) > 1.0:
            logger.info(
                "Positions still open for %s before credit removal, closing... (attempt %d)",
                mt5_login, attempt + 1,
            )
            await gateway.close_all_positions(mt5_login)
            await _asyncio.sleep(2)
            continue

        logger.info(
            "Removing credit: login=%s amount=%.2f (attempt %d)",
            mt5_login, account.credit, attempt + 1,
        )
        await gateway.remove_credit(
            mt5_login, account.credit,
            "Bonus cancelled - credit removal",
        )
        # Wait for MT5 to process, then verify
        await _asyncio.sleep(1.5)

        # Verify credit was actually removed
        check = await gateway.get_account_info(mt5_login)
        if check and check.credit <= 0.01:
            logger.info("Credit verified removed for %s", mt5_login)
            return
        logger.warning(
            "Credit removal not confirmed for %s: credit still %.2f (attempt %d)",
            mt5_login, check.credit if check else -1, attempt + 1,
        )

    logger.error("Failed to remove credit for %s after 5 attempts", mt5_login)


async def _get_active_bonuses(db: AsyncSession, mt5_login: str):
    result = await db.execute(
        select(Bonus).where(
            Bonus.mt5_login == mt5_login,
            Bonus.status == BonusStatus.ACTIVE,
        )
    )
    return result.scalars().all()


async def _get_active_type_c_bonuses(db: AsyncSession, mt5_login: str):
    result = await db.execute(
        select(Bonus).where(
            Bonus.mt5_login == mt5_login,
            Bonus.status == BonusStatus.ACTIVE,
            Bonus.bonus_type == "C",
        )
    )
    return result.scalars().all()
