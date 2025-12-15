from fastapi import APIRouter

from app.api.v1.endpoints import entries, health, reviews, search, solutions, tags

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(solutions.router, prefix="/solutions", tags=["solutions"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(search.router, prefix="/search", tags=["search"])

