from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.audit_log import EventType, ActorType


class AuditLogRead(BaseModel):
    id: int
    actor_type: ActorType
    actor_id: Optional[int]
    mt5_login: Optional[str]
    campaign_id: Optional[int]
    bonus_id: Optional[int]
    event_type: EventType
    before_state: Optional[dict]
    after_state: Optional[dict]
    metadata_: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    mt5_login: Optional[str] = None
    campaign_id: Optional[int] = None
    bonus_id: Optional[int] = None
    event_type: Optional[EventType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
