import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console
from rich.logging import RichHandler
import logging

from app.config import settings
from app.routers import health, environments, scaling, blueprints, events, incidents, finops, alerts, chaos
from app.services.aws.eb_client import EBClient

logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger("spikeshield")
console = Console()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(environments.router, prefix="/api/v1")
app.include_router(scaling.router, prefix="/api/v1")
app.include_router(blueprints.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(finops.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(chaos.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting SpikeShield Backend...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SpikeShield Backend...")

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"], summary="Root health check for EB ALB / Nginx")
async def root_health():
    """
    Root-level health check required by:
    - Elastic Beanstalk ALB target group health checks
    - Nginx upstream health probes (.platform/hooks)
    - Docker HEALTHCHECK
    """
    return {"status": "ok", "version": settings.APP_VERSION, "timestamp": __import__("datetime").datetime.utcnow().isoformat()}


@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    from app.routers.environments import list_environments
    from app.services.healer import get_active_incidents
    import random
    from datetime import timezone

    try:
        while True:
            now = datetime.now(timezone.utc).isoformat()
            envs = await list_environments()
            incidents = [i.model_dump(mode="json") for i in get_active_incidents()]
            metrics = []
            for env in envs:
                name = env["env_name"]
                base_rps = 820 if "prod" in name else (340 if "worker" in name else 120)
                rps = round(base_rps + random.uniform(-25, 35), 1)
                metrics.append({
                    "env_name": name,
                    "timestamp": now,
                    "rps": rps,
                    "p99_latency_ms": round(12.0 + random.uniform(0.5, 3.5), 1),
                    "cpu_percent": round(42.0 + random.uniform(-3.0, 5.0), 1),
                    "five_xx_rate": round(max(0.01, 0.05 + random.uniform(-0.02, 0.03)), 2),
                    "healthy_hosts": env["instances_info"].get("Ok", 4),
                })
            data = {
                "timestamp": now,
                "environments": envs,
                "metrics": metrics,
                "incidents": incidents,
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(4)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_paths(full_path: str):
    if full_path.startswith("api") or full_path.startswith("ws") or full_path in ("health", "docs", "redoc", "openapi.json"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    file_path = os.path.join(STATIC_DIR, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return RedirectResponse(url="/docs")


