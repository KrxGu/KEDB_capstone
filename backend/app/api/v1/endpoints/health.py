from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("", summary="API and dependency health status.")
async def healthcheck() -> dict[str, str]:
    """Expose minimal service metadata for container orchestration and probes."""
    return {
        "status": "ok",
        "service": settings.project_name,
        "environment": settings.environment,
    }
