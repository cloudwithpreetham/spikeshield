"""
SpikeShield Blueprints Router
Generates production-hardened Elastic Beanstalk configuration bundles.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.models.blueprint import BlueprintRequest, BlueprintResult, WorkloadProfile
from app.services.blueprint_gen import BlueprintGenerator

router = APIRouter(prefix="/blueprints", tags=["Blueprints"])
generator = BlueprintGenerator()

# Human-readable profile metadata
PROFILE_METADATA = {
    WorkloadProfile.HIGH_CONCURRENCY_UPI: {
        "value": WorkloadProfile.HIGH_CONCURRENCY_UPI.value,
        "label": "High-Concurrency UPI Webhook",
        "emoji": "🚀",
        "description": (
            "Optimized for UPI/payment callback floods. "
            "Handles 10k TPS bursts with upstream keepalive pools, "
            "fast-fail proxy timeouts (10s), and 200 r/s rate limiting. "
            "Min 3 instances (payment SLA). Deregistration delay: 10s."
        ),
        "use_cases": ["UPI callbacks", "Payment webhooks", "Razorpay/Paytm integrations"],
        "default_instance": "t3.medium",
        "default_min": 3,
        "default_max": 20,
    },
    WorkloadProfile.EDTECH_RESULT_PORTAL: {
        "value": WorkloadProfile.EDTECH_RESULT_PORTAL.value,
        "label": "EdTech Exam Result Portal",
        "emoji": "📚",
        "description": (
            "Built for 100x sudden traffic spikes on NEET/JEE/Board result day. "
            "Nginx micro-caching (30s stale-while-revalidate) absorbs the stampede, "
            "compute-optimized instances for PDF rendering, "
            "aggressive burst scaling to 50 instances in 60s cooldown."
        ),
        "use_cases": ["NEET/JEE results", "Board result portals", "EdTech dashboards"],
        "default_instance": "c5.large",
        "default_min": 2,
        "default_max": 50,
    },
    WorkloadProfile.D2C_FLASH_SALE: {
        "value": WorkloadProfile.D2C_FLASH_SALE.value,
        "label": "D2C Flash-Sale Storefront",
        "emoji": "🛒",
        "description": (
            "Diwali/Big Billion Days ready. "
            "Strict checkout rate-limiting (10 r/s, burst 20) prevents inventory racing. "
            "Product catalog micro-cached 30s. Pre-scale to 15 instances 20 min before sale."
        ),
        "use_cases": ["Diwali flash sales", "Big Billion Days", "D2C brand launches"],
        "default_instance": "t3.large",
        "default_min": 2,
        "default_max": 30,
    },
    WorkloadProfile.GENERIC_WEB: {
        "value": WorkloadProfile.GENERIC_WEB.value,
        "label": "Generic Web Application",
        "emoji": "🌐",
        "description": (
            "Balanced defaults for standard web applications. "
            "CPU-based scaling (70% threshold), standard keepalive settings, "
            "gzip enabled. Good starting point for any workload."
        ),
        "use_cases": ["General SaaS", "Internal tools", "APIs", "Marketing sites"],
        "default_instance": "t3.medium",
        "default_min": 2,
        "default_max": 10,
    },
}

# Pre-filled template defaults per profile
PROFILE_DEFAULTS = {
    WorkloadProfile.HIGH_CONCURRENCY_UPI: BlueprintRequest(
        profile=WorkloadProfile.HIGH_CONCURRENCY_UPI,
        app_port=8000,
        worker_processes=4,
        max_connections=4096,
        enable_rate_limiting=True,
        rate_limit_rps=200,
        enable_gzip=False,
        enable_brotli=False,
        enable_imdsv2=True,
        instance_type="t3.medium",
        min_instances=3,
        max_instances=20,
        enable_spot=True,
        spot_max_price="0.05",
    ),
    WorkloadProfile.EDTECH_RESULT_PORTAL: BlueprintRequest(
        profile=WorkloadProfile.EDTECH_RESULT_PORTAL,
        app_port=8000,
        worker_processes=6,
        max_connections=4096,
        enable_rate_limiting=True,
        rate_limit_rps=500,
        enable_gzip=True,
        enable_brotli=True,
        enable_imdsv2=True,
        instance_type="c5.large",
        min_instances=2,
        max_instances=50,
        enable_spot=True,
        spot_max_price="0.07",
    ),
    WorkloadProfile.D2C_FLASH_SALE: BlueprintRequest(
        profile=WorkloadProfile.D2C_FLASH_SALE,
        app_port=8000,
        worker_processes=4,
        max_connections=4096,
        enable_rate_limiting=True,
        rate_limit_rps=200,
        enable_gzip=True,
        enable_brotli=False,
        enable_imdsv2=True,
        instance_type="t3.large",
        min_instances=2,
        max_instances=30,
        enable_spot=True,
        spot_max_price="0.06",
    ),
    WorkloadProfile.GENERIC_WEB: BlueprintRequest(
        profile=WorkloadProfile.GENERIC_WEB,
        app_port=8000,
        worker_processes=4,
        max_connections=1024,
        enable_rate_limiting=True,
        rate_limit_rps=100,
        enable_gzip=True,
        enable_brotli=False,
        enable_imdsv2=True,
        instance_type="t3.medium",
        min_instances=2,
        max_instances=10,
        enable_spot=True,
        spot_max_price="0.04",
    ),
}


@router.post("/generate", summary="Generate a golden-path EB configuration bundle")
async def generate_blueprint(req: BlueprintRequest) -> BlueprintResult:
    """
    Generate a production-hardened Elastic Beanstalk configuration bundle
    for the selected workload profile.

    Returns all config files as strings:
    - `nginx_config` → `.platform/nginx/conf.d/app.conf`
    - `ebextension_capacity` → `.ebextensions/01_capacity.config`
    - `ebextension_cloudwatch` → `.ebextensions/02_cloudwatch.config`
    - `ebextension_security` → `.ebextensions/03_security.config`
    - `platform_predeploy_hook` → `.platform/hooks/predeploy/01_warmup.sh`
    - `platform_postdeploy_hook` → `.platform/hooks/postdeploy/01_smoketest.sh`
    - `procfile` → `Procfile`
    """
    return generator.generate(req)


@router.get("/profiles", summary="List available workload profiles with metadata")
async def list_profiles() -> list[dict]:
    """Returns all workload profiles with labels, descriptions, and use cases."""
    return list(PROFILE_METADATA.values())


@router.get(
    "/templates/{profile}",
    summary="Get pre-filled BlueprintRequest for a profile",
)
async def get_template(profile: WorkloadProfile) -> BlueprintRequest:
    """
    Returns an opinionated BlueprintRequest pre-filled with recommended
    defaults for the selected workload profile. Use as starting point in the UI.
    """
    return PROFILE_DEFAULTS.get(profile, BlueprintRequest(profile=profile))
