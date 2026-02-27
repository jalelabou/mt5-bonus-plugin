from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReportQuery(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    campaign_id: Optional[int] = None
    mt5_group: Optional[str] = None


class BonusSummaryRow(BaseModel):
    campaign_id: int
    campaign_name: str
    bonus_type: str
    total_issued: int
    total_amount: float
    active_count: int
    cancelled_count: int
    expired_count: int
    converted_count: int


class ConversionProgressRow(BaseModel):
    bonus_id: int
    mt5_login: str
    campaign_name: str
    bonus_amount: float
    lots_required: float
    lots_traded: float
    percent_complete: float
    amount_converted: float
    amount_remaining: float


class CancellationRow(BaseModel):
    bonus_id: int
    mt5_login: str
    campaign_name: str
    bonus_amount: float
    reason: str
    cancelled_at: datetime


class LeverageRow(BaseModel):
    bonus_id: int
    mt5_login: str
    campaign_name: str
    original_leverage: int
    adjusted_leverage: int
    status: str
