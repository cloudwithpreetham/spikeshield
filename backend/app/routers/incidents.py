"""
SpikeShield Incidents Router
Provides incident tracking, automated remediation triggers, and SRE runbook listings.
"""
from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter

from app.models.environment import IncidentEvent
from app.services.healer import get_active_incidents, SelfHealingEngine
from app.services.aws.eb_client import EBClient
from app.services.aws.cloudwatch import CloudWatchClient
from app.config import settings

router = APIRouter(prefix="/incidents", tags=["Incidents"])
eb_client = EBClient(settings)
cw_client = CloudWatchClient(settings)
healer = SelfHealingEngine(settings, eb_client=eb_client, cw_client=cw_client)

SAMPLE_INCIDENTS = [
    {
        "incident_id": "inc-01-mum-upi",
        "env_name": "spikeshield-prod",
        "severity": "high",
        "type": "velocity_surge",
        "description": "Sudden 4.2x request spike detected during UPI festive window. Peak RPS touched 1,840.",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
        "actions_taken": [
            "Slope acceleration detected (RequestCountPerTarget slope > +2.5)",
            "Pre-warmed Auto Scaling Group capacity from 2 to 4 instances proactively",
            "Nginx keepalive upstream pool utilized at 92% capacity",
            "Slack alert dispatched to #sre-alerts"
        ]
    },
    {
        "incident_id": "inc-02-mum-5xx",
        "env_name": "spikeshield-staging",
        "severity": "medium",
        "type": "5xx_error_budget",
        "description": "Faulty canary deploy caused ALB 5xx rate to reach 1.4% (budget: 1.0%).",
        "detected_at": "2026-10-07T05:00:00Z",
        "resolved_at": "2026-10-07T05:12:00Z",
        "actions_taken": [
            "ALB 5xx rate alarm breached 1.0% threshold",
            "Automated Blue/Green CNAME swap rollback triggered to previous-good version",
            "Degraded container instances drained and terminated",
            "Post-rollback 5xx rate stabilized to 0.02%"
        ]
    }
]


@router.get("", response_model=List[IncidentEvent])
async def list_incidents() -> List[dict]:
    active = [i.model_dump(mode="json") for i in get_active_incidents()]
    return active + SAMPLE_INCIDENTS


@router.post("/{incident_id}/rollback")
async def rollback(incident_id: str) -> Dict[str, Any]:
    envs = eb_client.list_environments()
    source_env = "spikeshield-staging"
    dest_env = "spikeshield-prod"
    if len(envs) >= 2:
        names = [e["env_name"] for e in envs]
        if "spikeshield-staging" in names and "spikeshield-prod" in names:
            source_env = "spikeshield-staging"
            dest_env = "spikeshield-prod"
        else:
            source_env = names[1]
            dest_env = names[0]

    incident = await healer.execute_rollback(source_env, dest_env)
    return {
        "status": "success",
        "incident_id": incident.incident_id,
        "message": f"Blue/Green CNAME rollback executed: {source_env} ↔ {dest_env}",
        "swapped_source": source_env,
        "swapped_target": dest_env,
        "actions_taken": incident.actions_taken
    }


@router.post("/{incident_id}/drain")
async def drain(incident_id: str) -> Dict[str, Any]:
    drained = await healer.drain_degraded_instances("spikeshield-prod")
    return {
        "status": "success",
        "message": f"Drained degraded instances for incident {incident_id}",
        "drained_instances": drained
    }


@router.post("/evaluate/{env_name}")
async def evaluate(env_name: str) -> Dict[str, Any]:
    actions = await healer.evaluate(env_name)
    return {
        "status": "evaluated",
        "env_name": env_name,
        "evaluations": actions
    }


@router.post("/{env_name}/evaluate")
async def evaluate_param(env_name: str) -> Dict[str, Any]:
    actions = await healer.evaluate(env_name)
    return {
        "status": "evaluated",
        "env_name": env_name,
        "evaluations": actions
    }


@router.get("/runbooks")
async def get_runbooks() -> List[Dict[str, Any]]:
    return [
        {
            "id": "rb-cname-swap",
            "name": "Zero-Downtime Blue/Green CNAME Rollback",
            "trigger": "ALB 5xx rate > 1.0% for 2 consecutive periods",
            "action": "Calls EB swap_environment_cnames API"
        },
        {
            "id": "rb-drain-degraded",
            "name": "Degraded Instance Draining",
            "trigger": "TargetResponseTime p99 > 3000ms or UnhealthyHostCount >= 1",
            "action": "Deregisters instance from target group, waits 20s, terminates EC2 node"
        },
        {
            "id": "rb-rate-limit-tighten",
            "name": "Dynamic Nginx Rate-Limit Tightening",
            "trigger": "Request velocity acceleration > 5x without scheduled event",
            "action": "Emits SQS message to drop Nginx rate-limit to 50r/s per client IP"
        }
    ]
