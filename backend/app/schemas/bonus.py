from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.bonus import BonusStatus


class BonusAssign(BaseModel):
    campaign_id: int
    mt5_login: str
    deposit_amount: Optional[float] = None


class BonusCancelRequest(BaseModel):
    reason: str = "admin_cancel"


class BonusOverrideLeverage(BaseModel):
    new_leverage: int


class BonusRead(BaseModel):
    id: int
    campaign_id: int
    campaign_name: Optional[str] = None
    mt5_login: str
    bonus_type: str
    bonus_amount: float
    original_leverage: Optional[int]
    adjusted_leverage: Optional[int]
    lots_required: Optional[float]
    lots_traded: float
    amount_converted: float
    status: BonusStatus
    assigned_at: datetime
    expires_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    created_at: datetime
    percent_converted: Optional[float] = None

    model_config = {"from_attributes": True}


class LotProgressRead(BaseModel):
    id: int
    deal_id: str
    symbol: str
    lots: float
    amount_converted: float
    created_at: datetime

    model_config = {"from_attributes": True}


class BonusDetailRead(BonusRead):
    lot_progress: List[LotProgressRead] = []
