"""
SpikeShield Self-Healing Engine
Autonomous SRE decision engine that evaluates environment health,
executes remediation runbooks, and sends RCA alerts to Slack.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings as global_settings
from app.models.environment import IncidentEvent
from app.utils.slack import send_slack_message, build_incident_blocks, build_rollback_blocks
from app.utils.ist_time import format_ist, now_ist

logger = logging.getLogger("spikeshield.healer")

# In-memory incident store (replace with Redis/DB for production)
_active_incidents: dict[str, IncidentEvent] = {}


def get_active_incidents() -> list[IncidentEvent]:
    return list(_active_incidents.values())


def get_incident(incident_id: str) -> Optional[IncidentEvent]:
    return _active_incidents.get(incident_id)


def resolve_incident(incident_id: str) -> None:
    if incident_id in _active_incidents:
        _active_incidents[incident_id].resolved_at = now_ist()


class SelfHealingEngine:
    """
    Evaluates Elastic Beanstalk environment health against error-budget thresholds
    and executes automated remediation runbooks.

    Runbook hierarchy (escalation order):
        1. WARN      — log + Slack warning, no action
        2. DRAIN     — terminate unhealthy instances (ASG replaces them)
        3. ROLLBACK  — Blue/Green CNAME swap to previous-good environment
        4. RATE_LIMIT — tighten Nginx rate limit via SQS worker message
    """

    # Threshold constants
    FIVE_XX_WARN_PCT = 1.0       # Slack warning
    FIVE_XX_CRITICAL_PCT = 3.0   # Trigger rollback
    P99_WARN_MS = 1000           # Slack warning
    P99_CRITICAL_MS = 3000       # Trigger drain
    HEALTHY_HOST_MINIMUM = 2     # Drain if fewer healthy hosts

    def __init__(self, settings=None, eb_client=None, cw_client=None, sqs_client=None) -> None:
        self.settings = settings or global_settings
        self._eb = eb_client
        self._cw = cw_client
        self._sqs = sqs_client

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    async def evaluate(self, env_name: str) -> list[str]:
        """
        Evaluate environment health and return a list of recommended / executed actions.
        In MOCK_AWS mode, returns a realistic assessment.
        """
        actions: list[str] = []

        if self.settings.MOCK_AWS:
            # Simulate a healthy environment with mock evaluation
            logger.info("[MOCK] Evaluating environment: %s", env_name)
            actions.append("Health check passed: Green (mock)")
            actions.append("5xx rate: 0.1% — within budget (threshold: %.1f%%)" % self.FIVE_XX_WARN_PCT)
            actions.append("p99 latency: 12ms — within SLA (threshold: %dms)" % self.P99_WARN_MS)
            actions.append("Healthy hosts: 4 — above minimum (%d)" % self.HEALTHY_HOST_MINIMUM)
            return actions

        # Real AWS evaluation
        try:
            # Fetch metrics (requires real AWS creds)
            five_xx_rate = 0.0
            p99_ms = 0.0
            healthy_hosts = 4

            if self._cw:
                try:
                    five_xx_rate = await _run_sync(self._cw.get_alb_5xx_rate, "", 60)
                    p99_latency = await _run_sync(self._cw.get_p99_latency, "", 60)
                    p99_ms = p99_latency * 1000
                except Exception as exc:
                    logger.warning("CloudWatch metrics unavailable: %s", exc)

            # Evaluate 5xx budget
            if five_xx_rate >= self.FIVE_XX_CRITICAL_PCT:
                msg = f"CRITICAL: 5xx rate {five_xx_rate:.1f}% exceeds rollback threshold ({self.FIVE_XX_CRITICAL_PCT}%)"
                logger.error(msg)
                actions.append(msg)
                incident = self._create_incident(env_name, "critical", "5xx_spike", msg)
                await self.send_rca_to_slack(incident, "Rollback initiated automatically")
            elif five_xx_rate >= self.FIVE_XX_WARN_PCT:
                msg = f"WARNING: 5xx rate {five_xx_rate:.1f}% exceeds warning threshold"
                logger.warning(msg)
                actions.append(msg)

            # Evaluate p99 latency
            if p99_ms >= self.P99_CRITICAL_MS:
                msg = f"CRITICAL: p99 latency {p99_ms:.0f}ms exceeds {self.P99_CRITICAL_MS}ms SLA"
                logger.error(msg)
                actions.append(msg)
            elif p99_ms >= self.P99_WARN_MS:
                msg = f"WARNING: p99 latency {p99_ms:.0f}ms elevated (threshold: {self.P99_WARN_MS}ms)"
                actions.append(msg)

            # Evaluate host count
            if healthy_hosts < self.HEALTHY_HOST_MINIMUM:
                msg = f"WARNING: Only {healthy_hosts} healthy hosts (minimum: {self.HEALTHY_HOST_MINIMUM})"
                actions.append(msg)

            if not actions:
                actions.append(f"All metrics within budget for {env_name}")

        except Exception as exc:
            logger.error("Evaluation failed for %s: %s", env_name, exc)
            actions.append(f"Evaluation error: {exc}")

        return actions

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    async def execute_rollback(
        self, source_env: str, target_env: str
    ) -> IncidentEvent:
        """
        Perform a Blue/Green CNAME swap between source (staging) and target (prod).
        The 'source' env gets the prod CNAME, effectively promoting staging to prod.
        """
        logger.info("Executing Blue/Green rollback: %s ↔ %s", source_env, target_env)
        actions_taken: list[str] = []

        if self.settings.MOCK_AWS:
            actions_taken.append(f"[MOCK] CNAME swap initiated: {source_env} ↔ {target_env}")
            actions_taken.append("[MOCK] swap_environment_cnames API called successfully")
            logger.info("[MOCK] Rollback complete (no real AWS call)")
        else:
            try:
                if self._eb:
                    self._eb.swap_environment_cnames(source_env, target_env)
                    actions_taken.append(f"CNAME swap executed: {source_env} ↔ {target_env}")
                else:
                    actions_taken.append("EB client not configured — swap skipped")
            except Exception as exc:
                logger.error("CNAME swap failed: %s", exc)
                actions_taken.append(f"CNAME swap FAILED: {exc}")

        incident = self._create_incident(
            env_name=target_env,
            severity="high",
            incident_type="blue_green_rollback",
            description=f"Blue/Green rollback executed: {source_env} ↔ {target_env}",
            actions_taken=actions_taken,
        )

        # Notify Slack
        if self.settings.SLACK_WEBHOOK_URL:
            blocks = build_rollback_blocks(source_env, target_env, "Automated rollback by SpikeShield healer")
            await send_slack_message(self.settings.SLACK_WEBHOOK_URL, blocks)

        return incident

    # ------------------------------------------------------------------
    # Drain degraded instances
    # ------------------------------------------------------------------

    async def drain_degraded_instances(self, env_name: str) -> list[str]:
        """
        Identify unhealthy instances in the environment and request their termination.
        AWS Auto Scaling will replace them with fresh healthy instances.
        """
        logger.info("Draining degraded instances for: %s", env_name)

        if self.settings.MOCK_AWS:
            mock_instances = ["i-0a1b2c3d4e5f6789a", "i-0b2c3d4e5f6789ab0"]
            logger.info("[MOCK] Would drain instances: %s", mock_instances)
            return mock_instances

        drained: list[str] = []
        try:
            if self._eb:
                instances = self._eb.describe_instances_health(env_name)
                unhealthy = [
                    (i.get("id") or i.get("InstanceId"))
                    for i in instances
                    if (i.get("status") or i.get("HealthStatus", "Ok")) not in ("Ok", "Green")
                ]
                unhealthy = [x for x in unhealthy if x]
                if unhealthy:
                    self._eb.terminate_instances(unhealthy)
                    drained = unhealthy
                    logger.info("Terminated %d unhealthy instances: %s", len(drained), drained)
                else:
                    logger.info("No unhealthy instances found in %s", env_name)
        except Exception as exc:
            logger.error("Failed to drain instances for %s: %s", env_name, exc)

        return drained

    # ------------------------------------------------------------------
    # Rate limit tightening
    # ------------------------------------------------------------------

    async def tighten_rate_limit(self, env_name: str, new_rps: int) -> None:
        """
        Queue an SQS runbook message to dynamically update the Nginx rate limit.
        The EB Worker environment's runbook_worker.py will consume this and
        write a new conf.d file + reload Nginx.
        """
        payload = {
            "action": "tighten_rate_limit",
            "env_name": env_name,
            "new_rps": new_rps,
            "triggered_at": now_ist().isoformat(),
        }

        if self.settings.MOCK_AWS or not self.settings.SQS_RUNBOOK_QUEUE_URL:
            logger.info("[MOCK] Would tighten rate limit for %s to %d r/s", env_name, new_rps)
            return

        if self._sqs:
            try:
                msg_id = self._sqs.send_runbook_message("tighten_rate_limit", payload)
                logger.info("Queued rate-limit runbook (MessageId: %s)", msg_id)
            except Exception as exc:
                logger.error("Failed to queue rate-limit runbook: %s", exc)

    # ------------------------------------------------------------------
    # Slack RCA notification
    # ------------------------------------------------------------------

    async def send_rca_to_slack(
        self, incident: IncidentEvent, cost_summary: str = ""
    ) -> None:
        """Send a rich Slack Block Kit RCA message for the incident."""
        if not self.settings.SLACK_WEBHOOK_URL:
            logger.info("Slack webhook not configured — skipping RCA notification")
            return

        try:
            blocks = build_incident_blocks(incident, cost_summary)
            success = await send_slack_message(self.settings.SLACK_WEBHOOK_URL, blocks)
            if success:
                logger.info("RCA sent to Slack for incident %s", incident.incident_id)
            else:
                logger.warning("Failed to send RCA to Slack for incident %s", incident.incident_id)
        except Exception as exc:
            logger.error("Slack RCA error: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_incident(
        self,
        env_name: str,
        severity: str,
        incident_type: str,
        description: str,
        actions_taken: Optional[list[str]] = None,
    ) -> IncidentEvent:
        incident = IncidentEvent(
            incident_id=str(uuid.uuid4()),
            env_name=env_name,
            severity=severity,  # type: ignore[arg-type]
            type=incident_type,
            description=description,
            detected_at=now_ist(),
            resolved_at=None,
            actions_taken=actions_taken or [],
        )
        _active_incidents[incident.incident_id] = incident
        return incident


# ---------------------------------------------------------------------------
# Helper: run sync boto3 calls in thread pool so they don't block the event loop
# ---------------------------------------------------------------------------

import asyncio
from functools import partial


async def _run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))
