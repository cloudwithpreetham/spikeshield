"""
SpikeShield Velocity Detector
Sliding-window request-velocity tracker with Redis-backed time series
and linear-regression slope computation for spike detection.
"""
from __future__ import annotations

import time
import math
import logging
from typing import Optional

logger = logging.getLogger("spikeshield.velocity")

# Redis key prefix for velocity sorted sets
_KEY_PREFIX = "spikeshield:velocity:"


class VelocityDetector:
    """
    Tracks request-per-second velocity for each EB environment.

    Data is stored as a Redis sorted set:
        key:   spikeshield:velocity:{env_name}
        score: Unix timestamp (float)
        member: "{timestamp}:{rps_value}"

    Falls back to in-memory deque if Redis is unavailable.
    """

    def __init__(self, settings, redis_client=None) -> None:
        self.settings = settings
        self._redis = redis_client          # Optional redis.Redis instance
        self._memory: dict[str, list[dict]] = {}   # in-memory fallback

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def record_request_count(self, env_name: str, count: float) -> None:
        """Store a (timestamp, rps) data point."""
        now = time.time()
        member = f"{now:.3f}:{count:.2f}"
        if self._redis:
            try:
                key = f"{_KEY_PREFIX}{env_name}"
                pipe = self._redis.pipeline()
                pipe.zadd(key, {member: now})
                # Prune entries older than 5× the window to keep memory bounded
                cutoff = now - self.settings.VELOCITY_WINDOW_SECONDS * 5
                pipe.zremrangebyscore(key, "-inf", cutoff)
                pipe.execute()
                return
            except Exception as exc:
                logger.debug("Redis unavailable, falling back to memory: %s", exc)

        # In-memory fallback
        bucket = self._memory.setdefault(env_name, [])
        bucket.append({"timestamp": now, "rps": count})
        cutoff = now - self.settings.VELOCITY_WINDOW_SECONDS * 5
        self._memory[env_name] = [p for p in bucket if p["timestamp"] >= cutoff]

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def _get_recent_points(self, env_name: str, window_seconds: int) -> list[dict]:
        """Return data points within the last `window_seconds`."""
        cutoff = time.time() - window_seconds
        if self._redis:
            try:
                key = f"{_KEY_PREFIX}{env_name}"
                raw = self._redis.zrangebyscore(key, cutoff, "+inf", withscores=True)
                points = []
                for member_bytes, score in raw:
                    member = member_bytes.decode() if isinstance(member_bytes, bytes) else member_bytes
                    try:
                        _, rps_str = member.rsplit(":", 1)
                        points.append({"timestamp": score, "rps": float(rps_str)})
                    except ValueError:
                        pass
                return points
            except Exception as exc:
                logger.debug("Redis read error: %s", exc)

        # In-memory fallback
        bucket = self._memory.get(env_name, [])
        return [p for p in bucket if p["timestamp"] >= cutoff]

    # ------------------------------------------------------------------
    # Velocity computation
    # ------------------------------------------------------------------

    def compute_velocity(self, env_name: str) -> float:
        """Return current RPS averaged over the last VELOCITY_WINDOW_SECONDS."""
        points = self._get_recent_points(env_name, self.settings.VELOCITY_WINDOW_SECONDS)
        if not points:
            return self._mock_rps(env_name)
        return sum(p["rps"] for p in points) / len(points)

    def compute_slope(self, env_name: str) -> float:
        """
        Return the rate of change of RPS (requests/sec/sec).
        Uses simple least-squares linear regression over the last 5 data points.
        Positive = rising traffic, Negative = falling traffic.
        """
        points = self._get_recent_points(env_name, self.settings.VELOCITY_WINDOW_SECONDS)
        if len(points) < 2:
            return 0.0

        # Use the last 5 points for the regression
        recent = sorted(points, key=lambda p: p["timestamp"])[-5:]
        n = len(recent)
        t0 = recent[0]["timestamp"]  # anchor so we don't lose precision

        xs = [p["timestamp"] - t0 for p in recent]
        ys = [p["rps"] for p in recent]

        x_mean = sum(xs) / n
        y_mean = sum(ys) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        denominator = sum((x - x_mean) ** 2 for x in xs)

        if denominator == 0.0:
            return 0.0
        return numerator / denominator

    def is_spike_detected(self, env_name: str, baseline_rps: float) -> bool:
        """
        Returns True if current velocity exceeds baseline by VELOCITY_SPIKE_THRESHOLD
        AND the slope is positive (still rising).
        """
        if baseline_rps <= 0:
            return False
        current = self.compute_velocity(env_name)
        slope = self.compute_slope(env_name)
        ratio = current / baseline_rps
        return ratio >= self.settings.VELOCITY_SPIKE_THRESHOLD and slope > 0

    def get_velocity_history(self, env_name: str, points: int = 20) -> list[dict]:
        """
        Return the last `points` data points as list of {timestamp, rps}.
        Falls back to synthetic mock data if no real data exists.
        """
        window = self.settings.VELOCITY_WINDOW_SECONDS * 5
        all_points = self._get_recent_points(env_name, window)

        if not all_points:
            return self._mock_history(env_name, points)

        sorted_pts = sorted(all_points, key=lambda p: p["timestamp"])
        return sorted_pts[-points:]

    # ------------------------------------------------------------------
    # Mock data (used when no real data exists yet)
    # ------------------------------------------------------------------

    def _mock_rps(self, env_name: str) -> float:
        """Return a stable mock RPS value based on env name hash."""
        base = 400 + (hash(env_name) % 200)
        # Add a small deterministic variation
        t_bucket = int(time.time() / 30)  # changes every 30s
        variation = math.sin(t_bucket + hash(env_name)) * 50
        return max(0.0, base + variation)

    def _mock_history(self, env_name: str, points: int) -> list[dict]:
        """Return synthetic time-series data for charting."""
        now = time.time()
        base_rps = self._mock_rps(env_name)
        history = []
        for i in range(points - 1, -1, -1):
            ts = now - i * (self.settings.VELOCITY_WINDOW_SECONDS / points)
            # Simulate a realistic-looking spike pattern
            noise = math.sin(i * 0.8 + hash(env_name)) * 30
            rps = max(0.0, base_rps + noise)
            history.append({"timestamp": ts, "rps": round(rps, 2)})
        return history
