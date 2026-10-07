"""
SpikeShield Events Router
Manages high-concurrency scheduled events (NEET results, IPL toss, Diwali sales)
and computes predictive auto-scaling pre-warming trigger times.
"""
from __future__ import annotations

import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter

from app.models.events import ScheduledEvent, EventCreateRequest, EventType

router = APIRouter(prefix="/events", tags=["Events"])

# In-memory storage with initial sample events
EVENTS_DB: List[ScheduledEvent] = [
    ScheduledEvent(
        event_id="evt-neet-2027",
        name="NEET UG 2027 Result Drop",
        type=EventType.EXAM_RESULT,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=3, minutes=30),
        expected_peak_rps=8500,
        env_name="spikeshield-prod",
        description="NTA NEET UG Result Declaration @ 4:00 PM IST. Anticipating 100x traffic spike.",
        is_active=True
    ),
    ScheduledEvent(
        event_id="evt-diwali-2026",
        name="Diwali Midnight Flash Sale (Big Billion Days)",
        type=EventType.FLASH_SALE,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
        expected_peak_rps=12000,
        env_name="spikeshield-prod",
        description="Festive midnight countdown. Heavy cart creation and payment callbacks.",
        is_active=True
    ),
    ScheduledEvent(
        event_id="evt-ipl-final",
        name="IPL 2027 Final Toss Surge",
        type=EventType.SPORTS_EVENT,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=5, hours=6),
        expected_peak_rps=9500,
        env_name="spikeshield-prod",
        description="7:00 PM IST toss window. Real-time live score poll and fantasy contest locks.",
        is_active=True
    )
]


@router.get("", response_model=List[ScheduledEvent])
async def list_events() -> List[ScheduledEvent]:
    return [e for e in EVENTS_DB if e.is_active]


@router.post("", response_model=ScheduledEvent)
async def create_event(req: EventCreateRequest) -> ScheduledEvent:
    event = ScheduledEvent(
        event_id=str(uuid.uuid4()),
        name=req.name,
        type=req.type,
        scheduled_at=req.scheduled_at,
        expected_peak_rps=req.expected_peak_rps,
        env_name=req.env_name,
        description=req.description,
        is_active=True
    )
    EVENTS_DB.append(event)
    return event


@router.delete("/{event_id}")
async def delete_event(event_id: str) -> Dict[str, Any]:
    global EVENTS_DB
    for e in EVENTS_DB:
        if e.event_id == event_id:
            e.is_active = False
            return {"status": "deleted", "event_id": event_id}
    return {"status": "not_found", "event_id": event_id}


@router.get("/upcoming", response_model=List[ScheduledEvent])
async def upcoming_events() -> List[ScheduledEvent]:
    now = datetime.now(timezone.utc)
    return [
        e for e in EVENTS_DB 
        if e.is_active and e.scheduled_at > now
    ]


@router.get("/presets")
async def preset_events() -> List[Dict[str, Any]]:
    return [
        {
            "name": "NEET 2027 Result",
            "type": "EXAM_RESULT",
            "expected_peak_rps": 8500,
            "description": "NTA Exam Result drop with PDF scorecards."
        },
        {
            "name": "IPL 2027 Final",
            "type": "SPORTS_EVENT",
            "expected_peak_rps": 9500,
            "description": "Peak toss and final over traffic surge."
        },
        {
            "name": "Diwali Sale 2026",
            "type": "FLASH_SALE",
            "expected_peak_rps": 12000,
            "description": "Midnight festive rush with payment callbacks."
        }
    ]
