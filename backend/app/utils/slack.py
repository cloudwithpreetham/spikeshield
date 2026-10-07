import httpx
import logging

logger = logging.getLogger("spikeshield.slack")


async def send_slack_message(webhook_url: str, blocks: list) -> bool:
    if not webhook_url:
        return False
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            res = await client.post(webhook_url, json={"blocks": blocks})
            return res.status_code == 200
        except Exception as e:
            logger.warning("Slack notification error: %s", e)
            return False


def build_incident_blocks(incident, rca_summary: str = "") -> list:
    sev_emoji = "🚨" if incident.severity in ("critical", "high") else "⚠️"
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{sev_emoji} SpikeShield Incident: {incident.type.upper()}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Environment:*\n`{incident.env_name}`"},
                {"type": "mrkdwn", "text": f"*Severity:*\n*{incident.severity.upper()}*"},
                {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident.incident_id}`"},
                {"type": "mrkdwn", "text": f"*Detected:*\n{incident.detected_at}"}
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{incident.description}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Automated RCA & Actions:*\n• " + "\n• ".join(incident.actions_taken or ["Self-healing evaluation underway"])
            }
        }
    ]


def build_prewarm_blocks(event_name: str, env_name: str, capacity: int, asg_name: str = "") -> list:
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚡ SpikeShield Predictive Pre-Warm Triggered",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Event:*\n*{event_name}*"},
                {"type": "mrkdwn", "text": f"*Target Capacity:*\n*{capacity} instances*"},
                {"type": "mrkdwn", "text": f"*Environment:*\n`{env_name}`"},
                {"type": "mrkdwn", "text": f"*ASG:*\n`{asg_name or 'AutoScalingGroup'}`"}
            ]
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Pre-warmed before flash crowd hit to eliminate 4-minute boot lag."}
            ]
        }
    ]


def build_rollback_blocks(source: str, target: str, reason: str) -> list:
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔄 Zero-Downtime Blue/Green CNAME Swap Executed",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Source (Staging):*\n`{source}`"},
                {"type": "mrkdwn", "text": f"*Target (Prod):*\n`{target}`"},
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:*\n{reason}"
            }
        }
    ]
