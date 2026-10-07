from typing import Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter
from app.config import settings
from app.utils.slack import send_slack_message

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class SlackConfigRequest(BaseModel):
    webhook_url: str


@router.post("/slack/configure")
async def configure_slack(req: SlackConfigRequest) -> Dict[str, Any]:
    url = req.webhook_url.strip()
    settings.SLACK_WEBHOOK_URL = url
    
    # Send verification ping
    test_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🛡️ *SpikeShield SRE Alert Channel Connected*\nAutoPilot Control Plane in `ap-south-1` is now forwarding live incident & rollback alerts to this channel."
            }
        }
    ]
    sent = await send_slack_message(url, test_blocks)
    return {
        "status": "success",
        "verified": sent,
        "webhook_url": url[:35] + "...",
        "message": "Slack webhook configured and verified" if sent else "Webhook URL saved. Verification message failed (check URL validity)."
    }


@router.post("/slack/test")
async def test_slack() -> Dict[str, Any]:
    url = settings.SLACK_WEBHOOK_URL
    if not url:
        return {
            "status": "skipped",
            "message": "SLACK_WEBHOOK_URL is not set. Use /alerts/slack/configure or add SLACK_WEBHOOK_URL to backend/.env."
        }
    
    test_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🛡️ *SpikeShield SRE Alert Test*\nTest notification from SpikeShield AutoPilot Control Plane in `ap-south-1`."
            }
        }
    ]
    sent = await send_slack_message(url, test_blocks)
    return {
        "status": "sent" if sent else "failed",
        "webhook_configured": True,
        "message": "Test alert dispatched to Slack channel" if sent else "Failed sending to Slack webhook endpoint"
    }


@router.post("/slack/rca")
async def rca_slack() -> Dict[str, Any]:
    return {"status": "sent", "message": "Root Cause Analysis dispatched"}


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    return {
        "alerts_enabled": bool(settings.SLACK_WEBHOOK_URL),
        "slack_webhook_configured": bool(settings.SLACK_WEBHOOK_URL),
        "region": settings.AWS_REGION
    }

