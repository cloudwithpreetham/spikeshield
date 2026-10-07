"""
SpikeShield AutoScaling Client
Manages AWS EC2 Auto Scaling Groups, desired capacity, and scheduled scaling actions.
"""
from __future__ import annotations

import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("spikeshield.asg")


class AutoScalingClient:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.client = None

        if not settings.MOCK_AWS:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self.client = boto3.client("autoscaling", **kwargs)

    def describe_asg(self, asg_name: str) -> Dict[str, Any]:
        if self.settings.MOCK_AWS or not self.client:
            return {"AutoScalingGroupName": asg_name, "MinSize": 2, "MaxSize": 10, "DesiredCapacity": 4}
        try:
            response = self.client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
            groups = response.get("AutoScalingGroups", [])
            return groups[0] if groups else {}
        except ClientError as e:
            logger.error("Failed to describe ASG %s: %s", asg_name, e)
            return {}

    def set_desired_capacity(self, asg_name: str, desired: int, honor_cooldown: bool = False) -> None:
        if self.settings.MOCK_AWS or not self.client:
            return
        try:
            self.client.set_desired_capacity(
                AutoScalingGroupName=asg_name,
                DesiredCapacity=desired,
                HonorCooldown=honor_cooldown
            )
        except ClientError as e:
            logger.error("Failed to set ASG capacity for %s to %d: %s", asg_name, desired, e)
            raise e

    def get_current_capacity(self, asg_name: str) -> Dict[str, int]:
        if self.settings.MOCK_AWS or not self.client:
            return {"min": 2, "max": 10, "desired": 4}
        asg = self.describe_asg(asg_name)
        return {
            "min": asg.get("MinSize", 0),
            "max": asg.get("MaxSize", 0),
            "desired": asg.get("DesiredCapacity", 0)
        }

    def put_scheduled_action(self, asg_name: str, action_name: str, scheduled_time: str, desired_capacity: int) -> None:
        if self.settings.MOCK_AWS or not self.client:
            return
        try:
            self.client.put_scheduled_update_group_action(
                AutoScalingGroupName=asg_name,
                ScheduledActionName=action_name,
                StartTime=scheduled_time,
                DesiredCapacity=desired_capacity
            )
        except ClientError as e:
            logger.error("Failed to schedule update group action: %s", e)
            raise e
