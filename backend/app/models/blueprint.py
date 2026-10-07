from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime

class WorkloadProfile(str, Enum):
    HIGH_CONCURRENCY_UPI = "HIGH_CONCURRENCY_UPI"
    EDTECH_RESULT_PORTAL = "EDTECH_RESULT_PORTAL"
    D2C_FLASH_SALE = "D2C_FLASH_SALE"
    GENERIC_WEB = "GENERIC_WEB"

class BlueprintRequest(BaseModel):
    profile: WorkloadProfile
    app_port: int = 8000
    worker_processes: int = 4
    max_connections: int = 1024
    enable_rate_limiting: bool = True
    rate_limit_rps: int = 100
    enable_gzip: bool = True
    enable_brotli: bool = False
    enable_imdsv2: bool = True
    instance_type: str = 't3.medium'
    min_instances: int = 2
    max_instances: int = 10
    enable_spot: bool = True
    spot_max_price: str = '0.05'
    custom_env_vars: Dict[str, str] = Field(default_factory=dict)

class BlueprintResult(BaseModel):
    profile: WorkloadProfile
    nginx_config: str
    ebextension_capacity: str
    ebextension_cloudwatch: str
    ebextension_security: str
    platform_predeploy_hook: str
    platform_postdeploy_hook: str
    procfile: str
    generated_at: datetime
