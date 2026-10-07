from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')

def now_ist() -> datetime:
    return datetime.now(IST)

def to_ist(dt: datetime) -> datetime:
    return dt.astimezone(IST)

def format_ist(dt: datetime) -> str:
    return dt.strftime('%a, %d %b %Y %I:%M %p IST')
