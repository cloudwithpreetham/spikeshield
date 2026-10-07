from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
import uuid

class EnvironmentHealth(BaseModel):
    env_name: str
    env_id: str
    status: str
    health: str
    health_status: str
    instances_info: dict
    causes: List[str]
    refreshed_at: datetime

class EnvironmentDetail(EnvironmentHealth):
    platform_arn: str
    solution_stack: str
    cname: str
    endpoint_url: str
    created_at: datetime
    updated_at: datetime
    tier: str

class ScalingAction(BaseModel):
    action_type: str
    reason: str
    desired_capacity: int
    triggered_at: datetime
    executed: bool

class IncidentEvent(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    env_name: str
    severity: Literal['low', 'medium', 'high', 'critical']
    type: str
    description: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    actions_taken: List[str]
