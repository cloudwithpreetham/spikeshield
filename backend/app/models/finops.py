from pydantic import BaseModel
from typing import List
from datetime import datetime

class InstanceCost(BaseModel):
    instance_type: str
    count: int
    hourly_rate_usd: float
    is_spot: bool
    hourly_cost_inr: float

class EnvironmentCost(BaseModel):
    env_name: str
    instances: List[InstanceCost]
    total_hourly_inr: float
    total_daily_inr: float
    cost_per_10k_requests: float
    usd_to_inr_rate: float = 84.0
    computed_at: datetime
