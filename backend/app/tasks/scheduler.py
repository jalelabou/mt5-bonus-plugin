import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import async_session
from app.tasks.expiry_checker import check_expired_bonuses

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_expiry_check():
    try:
        async with async_session() as db:
            count = await check_expired_bonuses(db)
            await db.commit()
            if count > 0:
                logger.info(f"Expired {count} bonus(es)")
    except Exception:
        logger.exception("Expiry check failed")


async def _run_monitor_cycle():
    from app.services.monitor_service import run_monitor_cycle
    try:
        async with async_session() as db:
            summary = await run_monitor_cycle(db)
            await db.commit()
            if any(v > 0 for k, v in summary.items() if k != "total"):
                logger.info("Monitor cycle: %s", summary)
    except Exception:
        logger.exception("Monitor cycle failed")


def start_scheduler():
    scheduler.add_job(
        _run_expiry_check,
        trigger=IntervalTrigger(hours=1),
        id="expiry_checker",
        name="Check expired bonuses",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_monitor_cycle,
        trigger=IntervalTrigger(seconds=0.3),
        id="account_monitor",
        name="Monitor accounts",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Background scheduler started (expiry + monitor @0.3s)")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Background scheduler stopped")
