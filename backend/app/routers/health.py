"""Health check endpoints for Cloud Run."""

from fastapi import APIRouter

router: APIRouter = APIRouter(tags=["health"])


@router.get("/ready")
async def readiness_probe() -> dict[str, str]:
    """Kubernetes/Cloud Run readiness probe."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_probe() -> dict[str, str]:
    """Kubernetes/Cloud Run liveness probe."""
    return {"status": "alive"}
