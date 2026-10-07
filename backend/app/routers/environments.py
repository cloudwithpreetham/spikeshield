"""
SpikeShield Environments Router
Provides Elastic Beanstalk environment management, health telemetry,
instance tracking, and CloudWatch metrics.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.environment import EnvironmentHealth, EnvironmentDetail
from app.services.aws.eb_client import EBClient
from app.services.aws.cloudwatch import CloudWatchClient
from app.config import settings

logger = logging.getLogger("spikeshield.environments")
router = APIRouter(prefix="/environments", tags=["Environments"])

eb_client = EBClient(settings)
cw_client = CloudWatchClient(settings)


class ProvisionRequest(BaseModel):
    app_name: str = "spikeshield-app"
    env_name: str = "spikeshield-prod"
    profile: str = "HIGH_CONCURRENCY_UPI"


@router.get("", response_model=List[EnvironmentHealth])
async def list_environments() -> List[dict]:
    """
    List all environments.
    When MOCK_AWS=False, queries real AWS Elastic Beanstalk describe_environments API.
    """
    envs = eb_client.list_environments()
    
    # If in real AWS mode and user hasn't deployed an EB app yet, return helpful guidance or empty list
    return envs


@router.get("/{env_name}", response_model=EnvironmentDetail)
async def get_environment(env_name: str) -> dict:
    envs = eb_client.list_environments()
    match = next((e for e in envs if e["env_name"] == env_name), None)
    now = datetime.now(timezone.utc).isoformat()
    if match:
        return match
    
    # If not directly matched, query health or build placeholder detail
    health_data = eb_client.describe_environment_health(env_name)
    return {
        "env_name": env_name,
        "env_id": health_data.get("EnvironmentId", f"e-{env_name}"),
        "status": health_data.get("Status", "Unknown"),
        "health": health_data.get("HealthStatus", "Grey"),
        "health_status": health_data.get("HealthStatus", "Unknown"),
        "instances_info": health_data.get("InstancesHealth", {"Ok": 0}),
        "causes": health_data.get("Causes", []),
        "platform_arn": "arn:aws:elasticbeanstalk:ap-south-1::platform/Python 3.11",
        "solution_stack": "64bit Amazon Linux 2023 running Python 3.11",
        "cname": f"{env_name}.ap-south-1.elasticbeanstalk.com",
        "endpoint_url": f"http://{env_name}.ap-south-1.elasticbeanstalk.com",
        "tier": "WebServer/Standard",
        "created_at": now,
        "updated_at": now,
        "refreshed_at": now,
    }


@router.get("/{env_name}/health")
async def get_env_health(env_name: str) -> Dict[str, Any]:
    return eb_client.describe_environment_health(env_name)


@router.get("/{env_name}/instances")
async def get_env_instances(env_name: str) -> List[Dict[str, Any]]:
    return eb_client.describe_instances_health(env_name)


@router.get("/{env_name}/events")
async def get_env_events(env_name: str) -> List[Dict[str, Any]]:
    return eb_client.get_environment_events(env_name)


@router.get("/{env_name}/metrics")
async def get_env_metrics(env_name: str) -> Dict[str, Any]:
    asg_name = env_name
    alb_dim = env_name
    try:
        res = eb_client.describe_environment_resources(env_name)
        asgs = res.get("AutoScalingGroups", [])
        if asgs:
            asg_name = asgs[0].get("Name", env_name)
        albs = res.get("LoadBalancers", [])
        if albs:
            raw_alb = albs[0].get("Name", "")
            if ":loadbalancer/" in raw_alb:
                alb_dim = raw_alb.split(":loadbalancer/")[-1]
            else:
                alb_dim = raw_alb
    except Exception as e:
        logger.debug("Failed resource resolution for metrics: %s", e)

    five_xx = cw_client.get_alb_5xx_rate(alb_dim)
    p99 = cw_client.get_p99_latency(alb_dim)
    rps = cw_client.get_request_count_per_target(alb_dim)
    cpu = cw_client.get_cpu_utilization(asg_name)

    instances = eb_client.describe_instances_health(env_name)
    healthy_count = len(instances) if instances else 1

    return {
        "env_name": env_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rps": rps,
        "p99_latency_ms": p99,
        "cpu_percent": cpu,
        "five_xx_rate": five_xx,
        "healthy_hosts": healthy_count,
    }


@router.post("/provision")
async def provision_environment(req: ProvisionRequest) -> Dict[str, Any]:
    """
    1-Click Provision an Elastic Beanstalk application & environment
    directly in ap-south-1 (Mumbai) with the chosen SpikeShield workload profile.
    """
    if settings.MOCK_AWS:
        return {
            "status": "success",
            "mode": "mock",
            "message": f"Simulated provisioning of {req.app_name} / {req.env_name}."
        }
    
    try:
        # 1. Create Application if it doesn't exist
        try:
            eb_client.create_application(req.app_name, "SpikeShield Managed Elastic Beanstalk Application")
        except Exception as e:
            logger.info("Application %s may already exist: %s", req.app_name, e)

        # 2. Create Environment
        cname = f"{req.env_name}-{datetime.now().strftime('%m%d%H%M')}"
        res = eb_client.create_environment(
            app_name=req.app_name,
            env_name=req.env_name,
            cname_prefix=cname
        )
        return {
            "status": "launching",
            "application_name": req.app_name,
            "environment_name": req.env_name,
            "cname_prefix": cname,
            "raw_response": res
        }
    except Exception as e:
        logger.error("Provisioning failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
