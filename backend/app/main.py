from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Placeholder for startup/shutdown hooks (workers, indexers, etc.)."""
    setup_logging(settings.log_level)
    yield


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
async def root_probe() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "KEDB API alive",
    }


def run() -> None:
    """Entrypoint for `poetry run kedb-api`."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.uvicorn_host,
        port=settings.uvicorn_port,
        reload=settings.environment == "local",
    )
