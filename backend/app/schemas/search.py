"""Search schemas for request/response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class SearchFilters(BaseModel):
    """Filters for search queries."""
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low|info)$")
    workflow_state: Optional[str] = Field(None, pattern="^(draft|in_review|published|retired|merged)$")
    created_by: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request payload."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    filters: Optional[SearchFilters] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class EntrySearchResult(BaseSchema):
    """Single entry search result."""
    id: UUID
    title: str
    description: str
    severity: str
    workflow_state: str
    created_by: str
    created_at: Optional[datetime] = None
    score: float = Field(..., description="Relevance score from Meilisearch")


class SolutionSearchResult(BaseSchema):
    """Single solution search result."""
    id: UUID
    title: str
    description: str
    solution_type: str
    entry_id: UUID
    created_at: Optional[datetime] = None
    score: float = Field(..., description="Relevance score from Meilisearch")


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    results: List[Dict[str, Any]]
    total: int
    query: str
    limit: int
    offset: int
    took_ms: int = Field(..., description="Query execution time in milliseconds")


class SolutionSearchFilters(BaseModel):
    """Filters for solution search."""
    solution_type: Optional[str] = Field(None, pattern="^(workaround|resolution)$")
    entry_id: Optional[UUID] = None


class SolutionSearchRequest(BaseModel):
    """Solution search request payload."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SolutionSearchFilters] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
