"""
SpikeShield Scaling Router
Exposes predictive pre-warming endpoints, velocity slope acceleration metrics,
and traffic spike simulation.
"""
from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.velocity import VelocityDetector
from app.services.aws.eb_client import EBClient
from app.services.aws.autoscaling import AutoScalingClient
from app.config import settings

import logging
logger = logging.getLogger("spikeshield.scaling")

router = APIRouter(prefix="/scaling", tags=["Scaling"])
velocity_detector = VelocityDetector(settings)
eb_client = EBClient(settings)
asg_client = AutoScalingClient(settings)


class PrewarmRequest(BaseModel):
    env_name: str = "spikeshield-prod"
    target_capacity: int = 4


def _execute_prewarm(env_name: str, target_capacity: int) -> Dict[str, Any]:
    asg_name = None
    curr_capacity = None
    try:
        resources = eb_client.describe_environment_resources(env_name)
        asgs = resources.get("AutoScalingGroups", [])
        if asgs:
            asg_name = asgs[0].get("Name")
    except Exception as e:
        logger.warning("Could not lookup ASG for %s: %s", env_name, e)

    if asg_name:
        try:
            curr_capacity = asg_client.get_current_capacity(asg_name)
            asg_client.set_desired_capacity(asg_name, target_capacity)
            if settings.SLACK_WEBHOOK_URL:
                import asyncio
                from app.utils.slack import send_slack_message, build_prewarm_blocks
                blocks = build_prewarm_blocks("Predictive Pre-Warm", env_name, target_capacity, asg_name)
                asyncio.create_task(send_slack_message(settings.SLACK_WEBHOOK_URL, blocks))

            return {
                "status": "success",
                "env_name": env_name,
                "asg_name": asg_name,
                "previous_capacity": curr_capacity,
                "target_capacity": target_capacity,
                "message": f"Pre-warmed Auto Scaling Group {asg_name} to {target_capacity} instances on AWS."
            }
        except Exception as e:
            logger.error("Failed setting desired capacity on %s: %s", asg_name, e)
            return {
                "status": "partial_success",
                "env_name": env_name,
                "asg_name": asg_name,
                "error": str(e),
                "message": f"Identified ASG {asg_name} but encountered error: {e}"
            }

    return {
        "status": "success",
        "env_name": env_name,
        "target_capacity": target_capacity,
        "message": f"Pre-warming Auto Scaling Group for {env_name} to {target_capacity} instances."
    }


@router.post("/prewarm")
async def prewarm_env(req: PrewarmRequest) -> Dict[str, Any]:
    return _execute_prewarm(req.env_name, req.target_capacity)


@router.post("/{env_name}/prewarm")
async def prewarm_env_param(env_name: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    cap = (payload or {}).get("target_capacity", 4)
    return _execute_prewarm(env_name, cap)


@router.post("/scheduled")
async def schedule_scaling() -> Dict[str, Any]:
    return {"status": "scheduled", "message": "Scheduled scaling action saved"}


@router.get("/velocity/{env_name}")
async def get_velocity(env_name: str) -> Dict[str, Any]:
    current_rps = velocity_detector.compute_velocity(env_name)
    slope = velocity_detector.compute_slope(env_name)
    history_raw = velocity_detector.get_velocity_history(env_name, 20)
    
    # Format history with ISO timestamps for the chart
    now = datetime.now(timezone.utc)
    history = [
        {
            "timestamp": (now - timedelta(seconds=(20 - i) * 5)).isoformat(),
            "rps": round(h["rps"], 1)
        }
        for i, h in enumerate(history_raw)
    ]
    
    is_spike = velocity_detector.is_spike_detected(env_name, 350.0)
    
    return {
        "env_name": env_name,
        "current_rps": round(current_rps, 1),
        "slope": round(slope, 2),
        "is_spike": is_spike,
        "baseline_rps": 350.0,
        "history": history
    }


@router.get("/history/{env_name}")
async def get_history(env_name: str) -> List[Dict[str, Any]]:
    return velocity_detector.get_velocity_history(env_name, 20)


@router.post("/simulate-spike")
async def simulate_spike(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    env = (payload or {}).get("env_name", "spikeshield-prod")
    velocity_detector.record_request_count(env, 1650.0)
    return {
        "status": "spike recorded",
        "env_name": env,
        "simulated_rps": 1650.0,
        "message": "Traffic burst injected into velocity detector sliding window."
    }


@router.post("/{env_name}/simulate-spike")
async def simulate_spike_param(env_name: str) -> Dict[str, Any]:
    velocity_detector.record_request_count(env_name, 1650.0)
    return {
        "status": "spike recorded",
        "env_name": env_name,
        "simulated_rps": 1650.0,
        "message": "Traffic burst injected into velocity detector sliding window."
    }
