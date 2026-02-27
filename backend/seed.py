"""Seed script to create initial admin user and test data."""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import hash_password
from app.db.database import async_session, engine
from app.db.base import Base
from app.models.user import AdminRole, AdminUser
from app.models.campaign import Campaign, CampaignStatus, BonusType, LotTrackingScope


async def seed():
    # Create tables directly (for dev without Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if admin already exists
        result = await db.execute(select(AdminUser).where(AdminUser.email == "admin@mt5bonus.com"))
        if result.scalar_one_or_none():
            print("Seed data already exists, skipping.")
            return

        # Create admin users
        users = [
            AdminUser(
                email="admin@mt5bonus.com",
                password_hash=hash_password("admin123"),
                full_name="Super Admin",
                role=AdminRole.SUPER_ADMIN,
            ),
            AdminUser(
                email="manager@mt5bonus.com",
                password_hash=hash_password("manager123"),
                full_name="Campaign Manager",
                role=AdminRole.CAMPAIGN_MANAGER,
            ),
            AdminUser(
                email="support@mt5bonus.com",
                password_hash=hash_password("support123"),
                full_name="Support Agent",
                role=AdminRole.SUPPORT_AGENT,
            ),
            AdminUser(
                email="viewer@mt5bonus.com",
                password_hash=hash_password("viewer123"),
                full_name="Read Only User",
                role=AdminRole.READ_ONLY,
            ),
        ]
        for u in users:
            db.add(u)
        await db.flush()

        admin = users[0]

        # Create sample campaigns
        campaigns = [
            Campaign(
                name="Welcome Bonus 100%",
                status=CampaignStatus.ACTIVE,
                bonus_type=BonusType.TYPE_B,
                bonus_percentage=100.0,
                max_bonus_amount=5000.0,
                min_deposit=100.0,
                max_deposit=10000.0,
                trigger_types=["auto_deposit", "registration"],
                target_mt5_groups=["demo\\standard", "demo\\premium"],
                one_bonus_per_account=True,
                max_concurrent_bonuses=1,
                notes="Welcome bonus for new accounts",
                created_by_id=admin.id,
            ),
            Campaign(
                name="VIP Leverage Boost 50%",
                status=CampaignStatus.ACTIVE,
                bonus_type=BonusType.TYPE_A,
                bonus_percentage=50.0,
                max_bonus_amount=25000.0,
                min_deposit=5000.0,
                trigger_types=["auto_deposit"],
                target_mt5_groups=["demo\\vip", "live\\vip"],
                one_bonus_per_account=False,
                max_concurrent_bonuses=2,
                expiry_days=90,
                notes="VIP dynamic leverage bonus",
                created_by_id=admin.id,
            ),
            Campaign(
                name="Trade & Earn Convertible",
                status=CampaignStatus.ACTIVE,
                bonus_type=BonusType.TYPE_C,
                bonus_percentage=50.0,
                max_bonus_amount=2500.0,
                min_deposit=500.0,
                lot_requirement=10.0,
                lot_tracking_scope=LotTrackingScope.POST_BONUS,
                trigger_types=["auto_deposit"],
                target_mt5_groups=["demo\\standard", "live\\standard"],
                one_bonus_per_account=True,
                max_concurrent_bonuses=1,
                expiry_days=60,
                notes="Convertible bonus - trade 10 lots to convert",
                created_by_id=admin.id,
            ),
            Campaign(
                name="Promo Code Special",
                status=CampaignStatus.ACTIVE,
                bonus_type=BonusType.TYPE_B,
                bonus_percentage=200.0,
                max_bonus_amount=1000.0,
                min_deposit=200.0,
                trigger_types=["promo_code"],
                promo_code="BONUS200",
                one_bonus_per_account=True,
                max_concurrent_bonuses=2,
                notes="200% bonus with promo code BONUS200",
                created_by_id=admin.id,
            ),
            Campaign(
                name="IB Referral Bonus",
                status=CampaignStatus.DRAFT,
                bonus_type=BonusType.TYPE_B,
                bonus_percentage=30.0,
                max_bonus_amount=3000.0,
                trigger_types=["agent_code"],
                agent_codes=["IB001", "IB002", "IB003"],
                one_bonus_per_account=True,
                max_concurrent_bonuses=1,
                notes="Agent/IB referral bonus - draft",
                created_by_id=admin.id,
            ),
        ]
        for c in campaigns:
            db.add(c)

        await db.commit()
        print("Seed data created successfully!")
        print("  Admin users: admin@mt5bonus.com / admin123")
        print("               manager@mt5bonus.com / manager123")
        print("               support@mt5bonus.com / support123")
        print("               viewer@mt5bonus.com / viewer123")
        print(f"  Campaigns: {len(campaigns)} created")


if __name__ == "__main__":
    asyncio.run(seed())
