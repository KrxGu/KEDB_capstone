"""Meilisearch client for lexical search operations."""
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.logging import logger


class MeilisearchClient:
    """Client for Meilisearch operations."""

    ENTRIES_INDEX = "entries"
    SOLUTIONS_INDEX = "solutions"

    def __init__(self):
        self.base_url = str(settings.meilisearch_url).rstrip("/")
        self.api_key = settings.meilisearch_master_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make HTTP request to Meilisearch."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self.headers,
                json=json,
                params=params,
            )
            if response.status_code >= 400:
                logger.error(f"Meilisearch error: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json() if response.text else {}

    async def ensure_indexes_exist(self) -> None:
        """Create indexes if they don't exist and configure settings."""
        await self._create_index_if_not_exists(
            self.ENTRIES_INDEX,
            primary_key="id",
            searchable_attributes=["title", "description", "symptoms", "root_cause"],
            filterable_attributes=["severity", "workflow_state", "created_by"],
            sortable_attributes=["created_at", "severity"],
        )

        await self._create_index_if_not_exists(
            self.SOLUTIONS_INDEX,
            primary_key="id",
            searchable_attributes=["title", "description", "steps_text"],
            filterable_attributes=["solution_type", "entry_id"],
            sortable_attributes=["created_at"],
        )

    async def _create_index_if_not_exists(
        self,
        index_name: str,
        primary_key: str,
        searchable_attributes: List[str],
        filterable_attributes: List[str],
        sortable_attributes: List[str],
    ) -> None:
        """Create index with configuration if it doesn't exist."""
        try:
            # Try to get index info
            await self._request("GET", f"/indexes/{index_name}")
            logger.info(f"Index '{index_name}' already exists")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Create index
                await self._request(
                    "POST",
                    "/indexes",
                    json={"uid": index_name, "primaryKey": primary_key},
                )
                logger.info(f"Created index '{index_name}'")
            else:
                raise

        # Update index settings
        settings_payload = {
            "searchableAttributes": searchable_attributes,
            "filterableAttributes": filterable_attributes,
            "sortableAttributes": sortable_attributes,
            "rankingRules": [
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
                "exactness",
            ],
        }

        await self._request(
            "PATCH",
            f"/indexes/{index_name}/settings",
            json=settings_payload,
        )
        logger.info(f"Updated settings for index '{index_name}'")

    # --- Entry Operations ---

    async def index_entry(self, entry_doc: Dict[str, Any]) -> None:
        """Add or update entry in search index."""
        await self._request(
            "POST",
            f"/indexes/{self.ENTRIES_INDEX}/documents",
            json=[entry_doc],
        )
        logger.info(f"Indexed entry {entry_doc.get('id')}")

    async def delete_entry(self, entry_id: str) -> None:
        """Remove entry from search index."""
        await self._request(
            "DELETE",
            f"/indexes/{self.ENTRIES_INDEX}/documents/{entry_id}",
        )
        logger.info(f"Deleted entry {entry_id} from index")

    async def search_entries(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search entries with optional filters."""
        payload = {
            "q": query,
            "limit": limit,
            "offset": offset,
            "showRankingScore": True,
        }

        if filters:
            filter_parts = []
            for key, value in filters.items():
                if value is not None:
                    filter_parts.append(f'{key} = "{value}"')
            if filter_parts:
                payload["filter"] = " AND ".join(filter_parts)

        return await self._request(
            "POST",
            f"/indexes/{self.ENTRIES_INDEX}/search",
            json=payload,
        )

    # --- Solution Operations ---

    async def index_solution(self, solution_doc: Dict[str, Any]) -> None:
        """Add or update solution in search index."""
        await self._request(
            "POST",
            f"/indexes/{self.SOLUTIONS_INDEX}/documents",
            json=[solution_doc],
        )
        logger.info(f"Indexed solution {solution_doc.get('id')}")

    async def delete_solution(self, solution_id: str) -> None:
        """Remove solution from search index."""
        await self._request(
            "DELETE",
            f"/indexes/{self.SOLUTIONS_INDEX}/documents/{solution_id}",
        )
        logger.info(f"Deleted solution {solution_id} from index")

    async def search_solutions(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search solutions with optional filters."""
        payload = {
            "q": query,
            "limit": limit,
            "offset": offset,
            "showRankingScore": True,
        }

        if filters:
            filter_parts = []
            for key, value in filters.items():
                if value is not None:
                    filter_parts.append(f'{key} = "{value}"')
            if filter_parts:
                payload["filter"] = " AND ".join(filter_parts)

        return await self._request(
            "POST",
            f"/indexes/{self.SOLUTIONS_INDEX}/search",
            json=payload,
        )

    async def health_check(self) -> bool:
        """Check if Meilisearch is healthy."""
        try:
            result = await self._request("GET", "/health")
            return result.get("status") == "available"
        except Exception as e:
            logger.error(f"Meilisearch health check failed: {e}")
            return False


# Singleton instance
meilisearch_client = MeilisearchClient()
