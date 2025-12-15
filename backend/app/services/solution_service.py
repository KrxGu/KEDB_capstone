"""Solution service for business logic."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import logger
from app.repositories.entry_repo import EntryRepository
from app.repositories.solution_repo import SolutionRepository
from app.schemas.solution import SolutionCreate, SolutionStepCreate, SolutionStepUpdate, SolutionUpdate
from app.search.meilisearch_client import meilisearch_client


class SolutionService:
    """Service for Solution business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SolutionRepository(db)
        self.entry_repo = EntryRepository(db)

    def _solution_to_search_doc(self, solution) -> dict:
        """Convert solution model to Meilisearch document."""
        steps_text = ""
        if hasattr(solution, "steps") and solution.steps:
            steps_text = " ".join([
                f"{s.action or ''} {s.expected_result or ''}"
                for s in solution.steps
            ])
        
        return {
            "id": str(solution.id),
            "title": solution.title,
            "description": solution.description or "",
            "solution_type": solution.solution_type,
            "entry_id": str(solution.entry_id),
            "created_at": solution.created_at.isoformat() if solution.created_at else None,
            "steps_text": steps_text,
        }

    async def _index_solution(self, solution) -> None:
        """Index solution in Meilisearch (fire and forget, log errors)."""
        try:
            doc = self._solution_to_search_doc(solution)
            await meilisearch_client.index_solution(doc)
        except Exception as e:
            logger.warning(f"Failed to index solution {solution.id}: {e}")

    async def _delete_solution_from_index(self, solution_id: UUID) -> None:
        """Remove solution from Meilisearch index."""
        try:
            await meilisearch_client.delete_solution(str(solution_id))
        except Exception as e:
            logger.warning(f"Failed to delete solution {solution_id} from index: {e}")

    async def create_solution(self, entry_id: UUID, solution_data: SolutionCreate, created_by: str):
        """Create solution for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        data_dict = solution_data.model_dump(exclude={"steps"})
        data_dict["entry_id"] = entry_id
        data_dict["created_by"] = created_by

        steps = None
        if solution_data.steps:
            steps = [s.model_dump() for s in solution_data.steps]

        solution = await self.repo.create_with_steps(data_dict, steps)
        full_solution = await self.repo.get_with_steps(solution.id)
        
        # Index in Meilisearch
        await self._index_solution(full_solution)
        
        return full_solution

    async def get_solution(self, solution_id: UUID):
        """Get solution by ID with steps."""
        solution = await self.repo.get_with_steps(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")
        return solution

    async def get_entry_solutions(self, entry_id: UUID):
        """Get all solutions for an entry."""
        entry = await self.entry_repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        return await self.repo.get_by_entry(entry_id)

    async def update_solution(self, solution_id: UUID, solution_data: SolutionUpdate):
        """Update solution."""
        solution = await self.repo.get(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")

        data_dict = solution_data.model_dump(exclude_unset=True)
        updated = await self.repo.update(solution_id, data_dict)
        full_solution = await self.repo.get_with_steps(solution_id)
        
        # Re-index in Meilisearch
        await self._index_solution(full_solution)
        
        return full_solution

    async def delete_solution(self, solution_id: UUID):
        """Delete solution."""
        solution = await self.repo.get(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")

        # Remove from search index
        await self._delete_solution_from_index(solution_id)

        return await self.repo.delete(solution_id)

    async def add_step(self, solution_id: UUID, step_data: SolutionStepCreate):
        """Add step to solution."""
        solution = await self.repo.get(solution_id)
        if not solution:
            raise NotFoundError(f"Solution {solution_id} not found")

        step = await self.repo.add_step(solution_id, step_data.model_dump())
        return step

    async def update_step(self, step_id: UUID, step_data: SolutionStepUpdate):
        """Update solution step."""
        step = await self.repo.get_step(step_id)
        if not step:
            raise NotFoundError(f"Step {step_id} not found")

        data_dict = step_data.model_dump(exclude_unset=True)
        return await self.repo.update_step(step_id, data_dict)

    async def delete_step(self, step_id: UUID):
        """Delete solution step."""
        step = await self.repo.get_step(step_id)
        if not step:
            raise NotFoundError(f"Step {step_id} not found")

        return await self.repo.delete_step(step_id)
