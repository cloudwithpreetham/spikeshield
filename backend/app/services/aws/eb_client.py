"""
SpikeShield Elastic Beanstalk Client
Orchestrates AWS Elastic Beanstalk environments, Enhanced Health metrics,
and Blue/Green CNAME swaps using boto3.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("spikeshield.eb")


class EBClient:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.client = None
        self.ec2_client = None

        if not settings.MOCK_AWS:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self.client = boto3.client("elasticbeanstalk", **kwargs)
            self.ec2_client = boto3.client("ec2", **kwargs)

    def list_environments(self) -> List[Dict[str, Any]]:
        """List all EB environments and map them to SpikeShield environment schema."""
        if self.settings.MOCK_AWS or not self.client:
            return self._mock_environments()

        try:
            kwargs = {}
            if self.settings.EB_APPLICATION_NAME:
                kwargs["ApplicationName"] = self.settings.EB_APPLICATION_NAME
            
            response = self.client.describe_environments(**kwargs)
            raw_envs = response.get("Environments", [])
            
            result = []
            now_iso = datetime.now(timezone.utc).isoformat()
            for env in raw_envs:
                # Optionally fetch enhanced health details
                instances_info = {"Ok": 1}
                causes = []
                env_name = env.get("EnvironmentName", "")
                
                try:
                    h_res = self.client.describe_environment_health(
                        EnvironmentName=env_name,
                        AttributeNames=["InstancesHealth", "Causes"]
                    )
                    instances_info = h_res.get("InstancesHealth", {"Ok": 1})
                    causes = h_res.get("Causes", [])
                except Exception as ex:
                    logger.debug("Could not get enhanced health for %s: %s", env_name, ex)

                created = env.get("DateCreated")
                created_iso = created.isoformat() if hasattr(created, "isoformat") else str(created)
                updated = env.get("DateUpdated")
                updated_iso = updated.isoformat() if hasattr(updated, "isoformat") else str(updated)

                tier_obj = env.get("Tier") or {}
                tier_str = f"{tier_obj.get('Name', 'WebServer')}/{tier_obj.get('Type', 'Standard')}"

                result.append({
                    "env_name": env_name,
                    "env_id": env.get("EnvironmentId", ""),
                    "status": env.get("Status", "Unknown"),
                    "health": env.get("Health", "Grey"),
                    "health_status": env.get("HealthStatus", "Unknown"),
                    "instances_info": instances_info,
                    "causes": causes,
                    "platform_arn": env.get("PlatformArn", ""),
                    "solution_stack": env.get("SolutionStackName", ""),
                    "cname": env.get("CNAME", ""),
                    "endpoint_url": env.get("EndpointURL", f"http://{env.get('CNAME', '')}"),
                    "tier": tier_str,
                    "created_at": created_iso,
                    "updated_at": updated_iso,
                    "refreshed_at": now_iso,
                })
            return result
        except Exception as e:
            logger.error("Failed to describe EB environments: %s", e)
            return []

    def describe_environment_health(self, env_name: str) -> Dict[str, Any]:
        if self.settings.MOCK_AWS or not self.client:
            return {
                "EnvironmentName": env_name,
                "HealthStatus": "Ok",
                "Status": "Ready",
                "InstancesHealth": {"Ok": 4, "Info": 0, "Warning": 0, "Degraded": 0, "Severe": 0},
                "Causes": [],
                "RefreshedAt": datetime.now(timezone.utc).isoformat()
            }
        try:
            return self.client.describe_environment_health(
                EnvironmentName=env_name,
                AttributeNames=["All"]
            )
        except Exception as e:
            logger.error("Failed to describe health for %s: %s", env_name, e)
            return {}

    def describe_instances_health(self, env_name: str) -> List[Dict[str, Any]]:
        """Return instance-level health information normalized for frontend."""
        if self.settings.MOCK_AWS or not self.client:
            return [
                {
                    "id": "i-mock001",
                    "instance_type": "t3.medium",
                    "availability_zone": "ap-south-1a",
                    "health": "Green",
                    "status": "Ok",
                },
                {
                    "id": "i-mock002",
                    "instance_type": "t3.medium",
                    "availability_zone": "ap-south-1b",
                    "health": "Green",
                    "status": "Ok",
                },
            ]
        try:
            res = self.client.describe_instances_health(
                EnvironmentName=env_name,
                AttributeNames=["All"]
            )
            raw_instances = res.get("InstanceHealthList", [])
            result = []
            for inst in raw_instances:
                result.append({
                    "id": inst.get("InstanceId", ""),
                    "instance_type": inst.get("InstanceType", "t3.micro"),
                    "availability_zone": inst.get("AvailabilityZone", "ap-south-1"),
                    "health": inst.get("Color", "Green"),
                    "status": inst.get("HealthStatus", "Ok"),
                    "causes": inst.get("Causes", []),
                })
            return result
        except Exception as e:
            logger.error("Failed to describe instances health for %s: %s", env_name, e)
            return []

    def describe_environment_resources(self, env_name: str) -> Dict[str, Any]:
        """Query AWS Elastic Beanstalk for real underlying ASG, ALB, and Instance resources."""
        if self.settings.MOCK_AWS or not self.client:
            return {
                "AutoScalingGroups": [{"Name": f"awseb-{env_name}-asg"}],
                "LoadBalancers": [{"Name": f"awseb-{env_name}-alb"}],
                "Instances": [{"Id": "i-mock123"}]
            }
        try:
            res = self.client.describe_environment_resources(EnvironmentName=env_name)
            return res.get("EnvironmentResources", {})
        except Exception as e:
            logger.error("Failed to describe environment resources for %s: %s", env_name, e)
            return {}


    def get_environment_events(self, env_name: str, max_records: int = 20) -> List[Dict[str, Any]]:
        """Return EB environment events normalized with ISO dates."""
        if self.settings.MOCK_AWS or not self.client:
            return [
                {
                    "event_date": datetime.now(timezone.utc).isoformat(),
                    "severity": "INFO",
                    "message": f"Environment {env_name} operating normally."
                }
            ]
        try:
            res = self.client.describe_events(EnvironmentName=env_name, MaxRecords=max_records)
            raw_events = res.get("Events", [])
            result = []
            for e in raw_events:
                dt = e.get("EventDate")
                dt_iso = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
                result.append({
                    "event_date": dt_iso,
                    "severity": e.get("Severity", "INFO"),
                    "message": e.get("Message", "")
                })
            return result
        except ClientError as e:
            logger.error("Failed to describe events for %s: %s", env_name, e)
            return []

    def swap_environment_cnames(self, source_env: str, dest_env: str) -> Dict[str, Any]:
        """Perform Zero-Downtime Blue/Green CNAME swap between two EB environments."""
        if self.settings.MOCK_AWS or not self.client:
            return {"Status": "Swapping (Mock)", "Source": source_env, "Destination": dest_env}
        try:
            self.client.swap_environment_cnames(
                SourceEnvironmentName=source_env,
                DestinationEnvironmentName=dest_env
            )
            return {"Status": "Success", "Source": source_env, "Destination": dest_env}
        except ClientError as e:
            logger.error("CNAME swap failed between %s and %s: %s", source_env, dest_env, e)
            raise e

    def terminate_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Terminate unhealthy EC2 instances (ASG replaces them automatically)."""
        if self.settings.MOCK_AWS or not self.ec2_client:
            return {"TerminatedInstances": instance_ids}
        try:
            return self.ec2_client.terminate_instances(InstanceIds=instance_ids)
        except ClientError as e:
            logger.error("Failed to terminate instances %s: %s", instance_ids, e)
            raise e

    def create_application(self, app_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new Elastic Beanstalk Application."""
        if self.settings.MOCK_AWS or not self.client:
            return {"ApplicationName": app_name}
        try:
            res = self.client.create_application(
                ApplicationName=app_name,
                Description=description or "Created by SpikeShield Control Plane"
            )
            return res.get("Application", {})
        except ClientError as e:
            logger.error("Failed to create application %s: %s", app_name, e)
            raise e

    def create_environment(
        self,
        app_name: str,
        env_name: str,
        solution_stack_name: str = "64bit Amazon Linux 2023 v4.13.9 running Python 3.11",
        option_settings: Optional[List[Dict[str, str]]] = None,
        cname_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an Elastic Beanstalk Environment with option settings."""
        if self.settings.MOCK_AWS or not self.client:
            return {"EnvironmentName": env_name, "ApplicationName": app_name, "Status": "Launching"}
        try:
            kwargs: Dict[str, Any] = {
                "ApplicationName": app_name,
                "EnvironmentName": env_name,
                "SolutionStackName": solution_stack_name,
            }
            if option_settings:
                kwargs["OptionSettings"] = option_settings
            if cname_prefix:
                kwargs["CNAMEPrefix"] = cname_prefix
            return self.client.create_environment(**kwargs)
        except ClientError as e:
            logger.error("Failed to create environment %s: %s", env_name, e)
            raise e

    def _mock_environments(self) -> List[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        return [
            {
                "env_name": "spikeshield-prod",
                "env_id": "e-mum-prod01",
                "status": "Ready",
                "health": "Green",
                "health_status": "Ok",
                "instances_info": {"Ok": 4, "Info": 0, "Warning": 0, "Degraded": 0, "Severe": 0},
                "causes": [],
                "platform_arn": "arn:aws:elasticbeanstalk:ap-south-1::platform/Python 3.11",
                "solution_stack": "64bit Amazon Linux 2023 running Python 3.11",
                "cname": "spikeshield-prod.ap-south-1.elasticbeanstalk.com",
                "endpoint_url": "http://spikeshield-prod.ap-south-1.elasticbeanstalk.com",
                "tier": "WebServer/Standard",
                "created_at": "2026-09-01T04:00:00Z",
                "updated_at": "2026-10-07T06:30:00Z",
                "refreshed_at": now_iso,
            }
        ]
