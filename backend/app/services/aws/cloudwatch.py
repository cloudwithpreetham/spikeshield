"""
SpikeShield CloudWatch Client
Queries real-time ALB 5xx error rates, p99 TargetResponseTime, and ASG metrics
from AWS CloudWatch using boto3.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("spikeshield.cloudwatch")


class CloudWatchClient:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.client = None

        if not settings.MOCK_AWS:
            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self.client = boto3.client("cloudwatch", **kwargs)

    def get_alb_5xx_rate(self, load_balancer_arn: str, period_seconds: int = 60) -> float:
        """Calculate 5xx error percentage over total requests from ALB."""
        if self.settings.MOCK_AWS or not self.client:
            return round(random.uniform(0.02, 0.12), 2)

        try:
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(minutes=5)

            # Query 5xx Count
            res_5xx = self.client.get_metric_statistics(
                Namespace="AWS/ApplicationELB",
                MetricName="HTTPCode_Target_5XX_Count",
                Dimensions=[{"Name": "LoadBalancer", "Value": load_balancer_arn}],
                StartTime=start_time,
                EndTime=now,
                Period=period_seconds,
                Statistics=["Sum"]
            )
            points_5xx = res_5xx.get("Datapoints", [])
            total_5xx = points_5xx[-1]["Sum"] if points_5xx else 0.0

            # Query Total Request Count
            res_req = self.client.get_metric_statistics(
                Namespace="AWS/ApplicationELB",
                MetricName="RequestCount",
                Dimensions=[{"Name": "LoadBalancer", "Value": load_balancer_arn}],
                StartTime=start_time,
                EndTime=now,
                Period=period_seconds,
                Statistics=["Sum"]
            )
            points_req = res_req.get("Datapoints", [])
            total_req = points_req[-1]["Sum"] if points_req else 1.0

            if total_req <= 0:
                return 0.0
            return round((total_5xx / total_req) * 100, 2)
        except Exception as e:
            logger.error("Failed to query ALB 5xx rate: %s", e)
            return 0.0

    def get_p99_latency(self, load_balancer_arn: str, period_seconds: int = 60) -> float:
        """Return TargetResponseTime p99 in milliseconds."""
        if self.settings.MOCK_AWS or not self.client:
            return round(random.uniform(10.0, 16.5), 1)

        try:
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(minutes=5)
            res = self.client.get_metric_statistics(
                Namespace="AWS/ApplicationELB",
                MetricName="TargetResponseTime",
                Dimensions=[{"Name": "LoadBalancer", "Value": load_balancer_arn}],
                StartTime=start_time,
                EndTime=now,
                Period=period_seconds,
                ExtendedStatistics=["p99"]
            )
            points = res.get("Datapoints", [])
            if points:
                return round(points[-1].get("ExtendedStatistics", {}).get("p99", 0.0) * 1000, 1)
            return 12.0
        except Exception as e:
            logger.error("Failed to query p99 latency: %s", e)
            return 12.0

    def get_request_count_per_target(self, target_group_arn: str, period_seconds: int = 60) -> float:
        """Return RequestCountPerTarget from ALB Target Group."""
        if self.settings.MOCK_AWS or not self.client:
            return round(random.uniform(420.0, 680.0), 1)

        try:
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(minutes=5)
            res = self.client.get_metric_statistics(
                Namespace="AWS/ApplicationELB",
                MetricName="RequestCountPerTarget",
                Dimensions=[{"Name": "TargetGroup", "Value": target_group_arn}],
                StartTime=start_time,
                EndTime=now,
                Period=period_seconds,
                Statistics=["Sum"]
            )
            points = res.get("Datapoints", [])
            return round(points[-1]["Sum"], 1) if points else 0.0
        except Exception as e:
            logger.error("Failed to query RequestCountPerTarget: %s", e)
            return 0.0

    def get_cpu_utilization(self, asg_name: str, period_seconds: int = 60) -> float:
        """Return average EC2 CPU Utilization across the Auto Scaling Group."""
        if self.settings.MOCK_AWS or not self.client:
            return round(random.uniform(38.0, 48.0), 1)

        try:
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(minutes=5)
            res = self.client.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "AutoScalingGroupName", "Value": asg_name}],
                StartTime=start_time,
                EndTime=now,
                Period=period_seconds,
                Statistics=["Average"]
            )
            points = res.get("Datapoints", [])
            return round(points[-1]["Average"], 1) if points else 0.0
        except Exception as e:
            logger.error("Failed to query CPU utilization: %s", e)
            return 0.0

    def put_custom_metric(self, namespace: str, metric_name: str, value: float, unit: str = "Count") -> None:
        if self.settings.MOCK_AWS or not self.client:
            return
        try:
            self.client.put_metric_data(
                Namespace=namespace,
                MetricData=[{"MetricName": metric_name, "Value": value, "Unit": unit}]
            )
        except Exception as e:
            logger.warning("Failed to put custom metric: %s", e)

    def list_alarms_in_alarm(self) -> List[Dict[str, Any]]:
        if self.settings.MOCK_AWS or not self.client:
            return []
        try:
            return self.client.describe_alarms(StateValue="ALARM").get("MetricAlarms", [])
        except Exception as e:
            logger.error("Failed to list alarms: %s", e)
            return []
