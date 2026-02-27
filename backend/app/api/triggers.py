from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.trigger_service import (
    process_deposit_trigger,
    process_promo_code_trigger,
    process_registration_trigger,
)

router = APIRouter(prefix="/api/triggers", tags=["triggers"])


class DepositEvent(BaseModel):
    mt5_login: str
    deposit_amount: float
    agent_code: Optional[str] = None


class RegistrationEvent(BaseModel):
    mt5_login: str


class PromoCodeEvent(BaseModel):
    mt5_login: str
    promo_code: str
    deposit_amount: Optional[float] = None


@router.post("/deposit")
async def deposit_trigger(body: DepositEvent, db: AsyncSession = Depends(get_db)):
    results = await process_deposit_trigger(db, body.mt5_login, body.deposit_amount, body.agent_code)
    return {"results": results}


@router.post("/registration")
async def registration_trigger(body: RegistrationEvent, db: AsyncSession = Depends(get_db)):
    results = await process_registration_trigger(db, body.mt5_login)
    return {"results": results}


@router.post("/promo-code")
async def promo_code_trigger(body: PromoCodeEvent, db: AsyncSession = Depends(get_db)):
    results = await process_promo_code_trigger(
        db, body.mt5_login, body.promo_code, body.deposit_amount
    )
    return {"results": results}
