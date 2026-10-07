from fastapi import APIRouter
from datetime import datetime
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def get_health():
    return {"status": "ok", "version": settings.APP_VERSION, "timestamp": datetime.utcnow().isoformat()}

@router.get("/status")
async def get_status():
    return {"status": "ok", "redis": "connected", "aws": "mocked" if settings.MOCK_AWS else "connected"}
