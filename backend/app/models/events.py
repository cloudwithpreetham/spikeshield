from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class EventType(str, Enum):
    EXAM_RESULT = "EXAM_RESULT"
    FLASH_SALE = "FLASH_SALE"
    SPORTS_EVENT = "SPORTS_EVENT"
    BOOKING_WINDOW = "BOOKING_WINDOW"
    CUSTOM = "CUSTOM"

class ScheduledEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: EventType
    scheduled_at: datetime
    expected_peak_rps: int
    env_name: str
    description: str = ''
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class EventCreateRequest(BaseModel):
    name: str
    type: EventType
    scheduled_at: datetime
    expected_peak_rps: int
    env_name: str
    description: str = ''
