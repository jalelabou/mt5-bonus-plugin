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


def start_scheduler():
    scheduler.add_job(
        _run_expiry_check,
        trigger=IntervalTrigger(hours=1),
        id="expiry_checker",
        name="Check expired bonuses",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Background scheduler stopped")
