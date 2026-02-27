from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.campaign import BonusType, CampaignStatus, LotTrackingScope, TriggerType


class CampaignCreate(BaseModel):
    name: str
    bonus_type: BonusType
    bonus_percentage: float
    max_bonus_amount: Optional[float] = None
    min_deposit: Optional[float] = None
    max_deposit: Optional[float] = None
    lot_requirement: Optional[float] = None
    lot_tracking_scope: Optional[LotTrackingScope] = None
    symbol_filter: Optional[List[str]] = None
    per_trade_lot_minimum: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    expiry_days: Optional[int] = None
    target_mt5_groups: Optional[List[str]] = None
    target_countries: Optional[List[str]] = None
    trigger_types: List[str] = []
    promo_code: Optional[str] = None
    agent_codes: Optional[List[str]] = None
    one_bonus_per_account: bool = False
    max_concurrent_bonuses: int = 1
    notes: Optional[str] = None


class CampaignUpdate(CampaignCreate):
    name: Optional[str] = None
    bonus_type: Optional[BonusType] = None
    bonus_percentage: Optional[float] = None


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


class CampaignRead(BaseModel):
    id: int
    name: str
    status: CampaignStatus
    bonus_type: BonusType
    bonus_percentage: float
    max_bonus_amount: Optional[float]
    min_deposit: Optional[float]
    max_deposit: Optional[float]
    lot_requirement: Optional[float]
    lot_tracking_scope: Optional[LotTrackingScope]
    symbol_filter: Optional[List[str]]
    per_trade_lot_minimum: Optional[float]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    expiry_days: Optional[int]
    target_mt5_groups: Optional[List[str]]
    target_countries: Optional[List[str]]
    trigger_types: List[str]
    promo_code: Optional[str]
    agent_codes: Optional[List[str]]
    one_bonus_per_account: bool
    max_concurrent_bonuses: int
    notes: Optional[str]
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    active_bonus_count: Optional[int] = None

    model_config = {"from_attributes": True}


class CampaignListRead(BaseModel):
    id: int
    name: str
    status: CampaignStatus
    bonus_type: BonusType
    bonus_percentage: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    active_bonus_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
