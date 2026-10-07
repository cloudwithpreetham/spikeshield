"""
SpikeShield Chaos Router
Simulates flash-crowd traffic bursts and evaluates auto-scaling & self-healing responses.
"""
from __future__ import annotations

import asyncio
import time
import uuid
import logging
from typing import Dict, Any, List
from collections import deque
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("spikeshield.chaos")
router = APIRouter(prefix="/chaos", tags=["Chaos"])

JOBS: Dict[str, Dict[str, Any]] = {}
STOP_EVENTS: Dict[str, asyncio.Event] = {}


class ChaosRequest(BaseModel):
    target_url: str = "http://localhost:8000/health"
    duration_seconds: int = 60
    concurrent_users: int = 50
    ramp_up_seconds: int = 5


async def _load_test_worker(
    target_url: str,
    client: httpx.AsyncClient,
    stats: Dict[str, Any],
    stop_event: asyncio.Event,
    recent_latencies: deque,
    recent_requests: deque,
    recent_errors: deque
):
    while not stop_event.is_set():
        t0 = time.perf_counter()
        now = time.time()
        is_error = False
        try:
            resp = await client.get(target_url)
            if resp.status_code >= 400:
                is_error = True
        except Exception:
            is_error = True

        latency_ms = (time.perf_counter() - t0) * 1000.0

        recent_latencies.append((now, latency_ms))
        recent_requests.append(now)
        if is_error:
            recent_errors.append(now)

        stats["total_requests"] += 1
        if is_error:
            stats["total_errors"] += 1

        # Tiny yield to prevent CPU starvation across tasks
        await asyncio.sleep(0.005)


async def _run_load_test_job(job_id: str, req: ChaosRequest):
    stop_event = asyncio.Event()
    STOP_EVENTS[job_id] = stop_event

    recent_latencies = deque(maxlen=2000)
    recent_requests = deque(maxlen=2000)
    recent_errors = deque(maxlen=2000)

    stats = {
        "total_requests": 0,
        "total_errors": 0,
    }

    limits = httpx.Limits(max_connections=req.concurrent_users + 10, max_keepalive_connections=req.concurrent_users)
    timeout = httpx.Timeout(5.0, connect=3.0)

    start_time = time.time()
    end_time = start_time + req.duration_seconds

    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        # Spawn workers
        worker_count = max(1, min(req.concurrent_users, 200))
        tasks = [
            asyncio.create_task(
                _load_test_worker(
                    req.target_url,
                    client,
                    stats,
                    stop_event,
                    recent_latencies,
                    recent_requests,
                    recent_errors
                )
            )
            for _ in range(worker_count)
        ]

        try:
            while time.time() < end_time and not stop_event.is_set():
                now = time.time()
                # Calculate metrics over the last 2 seconds
                cutoff = now - 2.0

                while recent_requests and recent_requests[0] < cutoff:
                    recent_requests.popleft()
                while recent_errors and recent_errors[0] < cutoff:
                    recent_errors.popleft()
                while recent_latencies and recent_latencies[0][0] < cutoff:
                    recent_latencies.popleft()

                window_sec = max(0.5, min(2.0, now - start_time))
                current_rps = len(recent_requests) / window_sec
                error_count = len(recent_errors)
                error_rate = (error_count / len(recent_requests) * 100.0) if recent_requests else 0.0

                if recent_latencies:
                    avg_latency = sum(l[1] for l in recent_latencies) / len(recent_latencies)
                else:
                    avg_latency = 0.0

                JOBS[job_id].update({
                    "current_rps": round(current_rps, 1),
                    "error_rate_percent": round(error_rate, 1),
                    "avg_latency_ms": round(avg_latency, 1),
                    "total_requests": stats["total_requests"],
                    "total_errors": stats["total_errors"],
                })

                await asyncio.sleep(0.5)

        finally:
            stop_event.set()
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

            if JOBS[job_id].get("status") == "running":
                JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["current_rps"] = 0.0


@router.post("/spike")
async def chaos_spike(req: ChaosRequest) -> Dict[str, Any]:
    job_id = f"chaos-{uuid.uuid4().hex[:8]}"
    JOBS[job_id] = {
        "job_id": job_id,
        "target_url": req.target_url,
        "duration_seconds": req.duration_seconds,
        "concurrent_users": req.concurrent_users,
        "ramp_up_seconds": req.ramp_up_seconds,
        "status": "running",
        "current_rps": 0.0,
        "error_rate_percent": 0.0,
        "avg_latency_ms": 0.0,
        "total_requests": 0,
        "total_errors": 0,
    }

    asyncio.create_task(_run_load_test_job(job_id, req))
    return {"job_id": job_id, "status": "running"}


@router.get("/status/{job_id}")
async def chaos_status(job_id: str) -> Dict[str, Any]:
    job = JOBS.get(job_id)
    if not job:
        return {
            "job_id": job_id,
            "status": "completed",
            "current_rps": 0.0,
            "error_rate_percent": 0.0,
            "avg_latency_ms": 0.0,
        }
    return job


@router.post("/stop/{job_id}")
async def chaos_stop(job_id: str) -> Dict[str, Any]:
    if job_id in STOP_EVENTS:
        STOP_EVENTS[job_id].set()
    if job_id in JOBS:
        JOBS[job_id]["status"] = "stopped"
        JOBS[job_id]["current_rps"] = 0.0
    return {"status": "stopped", "job_id": job_id}
