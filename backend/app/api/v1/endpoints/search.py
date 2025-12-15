"""Search API endpoints."""
import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SolutionSearchRequest,
)
from app.search.meilisearch_client import meilisearch_client

router = APIRouter()


@router.post("/entries", response_model=SearchResponse)
async def search_entries(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search entries using Meilisearch.
    
    Supports:
    - Full-text search across title, description, symptoms, root_cause
    - Typo tolerance
    - Filters by severity, workflow_state, created_by
    """
    start_time = time.time()

    try:
        # Build filters dict
        filters = None
        if request.filters:
            filters = request.filters.model_dump(exclude_none=True)

        # Execute search
        result = await meilisearch_client.search_entries(
            query=request.query,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

        took_ms = int((time.time() - start_time) * 1000)

        # Transform results
        results = []
        for hit in result.get("hits", []):
            results.append({
                "id": hit.get("id"),
                "title": hit.get("title"),
                "description": hit.get("description"),
                "severity": hit.get("severity"),
                "workflow_state": hit.get("workflow_state"),
                "created_by": hit.get("created_by"),
                "created_at": hit.get("created_at"),
                "score": hit.get("_rankingScore", 0.0),
            })

        return SearchResponse(
            results=results,
            total=result.get("estimatedTotalHits", len(results)),
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            took_ms=took_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/solutions", response_model=SearchResponse)
async def search_solutions(
    request: SolutionSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search solutions using Meilisearch.
    
    Supports:
    - Full-text search across title, description, steps
    - Filters by solution_type, entry_id
    """
    start_time = time.time()

    try:
        # Build filters dict
        filters = None
        if request.filters:
            filters_dict = request.filters.model_dump(exclude_none=True)
            # Convert UUID to string for filter
            if "entry_id" in filters_dict and filters_dict["entry_id"]:
                filters_dict["entry_id"] = str(filters_dict["entry_id"])
            filters = filters_dict

        # Execute search
        result = await meilisearch_client.search_solutions(
            query=request.query,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )

        took_ms = int((time.time() - start_time) * 1000)

        # Transform results
        results = []
        for hit in result.get("hits", []):
            results.append({
                "id": hit.get("id"),
                "title": hit.get("title"),
                "description": hit.get("description"),
                "solution_type": hit.get("solution_type"),
                "entry_id": hit.get("entry_id"),
                "created_at": hit.get("created_at"),
                "score": hit.get("_rankingScore", 0.0),
            })

        return SearchResponse(
            results=results,
            total=result.get("estimatedTotalHits", len(results)),
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            took_ms=took_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/health")
async def search_health():
    """Check Meilisearch connection health."""
    is_healthy = await meilisearch_client.health_check()
    if is_healthy:
        return {"status": "ok", "service": "meilisearch"}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Meilisearch is not available",
        )


@router.post("/init-indexes", status_code=status.HTTP_201_CREATED)
async def initialize_indexes():
    """
    Initialize Meilisearch indexes with proper configuration.
    Call this once after first deployment or to reset index settings.
    """
    try:
        await meilisearch_client.ensure_indexes_exist()
        return {"status": "ok", "message": "Indexes initialized successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize indexes: {str(e)}",
        )
