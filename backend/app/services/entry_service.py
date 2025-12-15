"""Entry service for business logic."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, WorkflowError
from app.core.logging import logger
from app.repositories.entry_repo import EntryRepository
from app.schemas.entry import EntryCreate, EntryIncidentCreate, EntrySymptomCreate, EntryUpdate
from app.search.meilisearch_client import meilisearch_client


class EntryService:
    """Service for Entry business logic."""

    VALID_WORKFLOW_TRANSITIONS = {
        "draft": ["in_review", "retired"],
        "in_review": ["draft", "published", "retired"],
        "published": ["retired", "merged"],
        "retired": [],
        "merged": [],
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EntryRepository(db)

    def _entry_to_search_doc(self, entry) -> dict:
        """Convert entry model to Meilisearch document."""
        symptoms_text = ""
        if hasattr(entry, "symptoms") and entry.symptoms:
            symptoms_text = " ".join([s.symptom for s in entry.symptoms if s.symptom])
        
        return {
            "id": str(entry.id),
            "title": entry.title,
            "description": entry.description or "",
            "severity": entry.severity,
            "workflow_state": entry.workflow_state,
            "created_by": entry.created_by,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "root_cause": entry.root_cause or "",
            "symptoms": symptoms_text,
        }

    async def _index_entry(self, entry) -> None:
        """Index entry in Meilisearch (fire and forget, log errors)."""
        try:
            doc = self._entry_to_search_doc(entry)
            await meilisearch_client.index_entry(doc)
        except Exception as e:
            logger.warning(f"Failed to index entry {entry.id}: {e}")

    async def _delete_entry_from_index(self, entry_id: UUID) -> None:
        """Remove entry from Meilisearch index."""
        try:
            await meilisearch_client.delete_entry(str(entry_id))
        except Exception as e:
            logger.warning(f"Failed to delete entry {entry_id} from index: {e}")

    async def create_entry(self, entry_data: EntryCreate, created_by: str):
        """Create a new entry."""
        data_dict = entry_data.model_dump(exclude={"symptoms", "incidents"})
        data_dict["created_by"] = created_by
        data_dict["workflow_state"] = "draft"

        symptoms = None
        if entry_data.symptoms:
            symptoms = [s.model_dump() for s in entry_data.symptoms]

        entry = await self.repo.create_with_symptoms(data_dict, symptoms)

        if entry_data.incidents:
            for incident in entry_data.incidents:
                await self.repo.add_incident(entry.id, incident.model_dump())

        full_entry = await self.repo.get_with_relations(entry.id)
        
        # Index in Meilisearch
        await self._index_entry(full_entry)
        
        return full_entry

    async def get_entry(self, entry_id: UUID):
        """Get entry by ID with all relations."""
        entry = await self.repo.get_with_relations(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")
        return entry

    async def list_entries(
        self,
        skip: int = 0,
        limit: int = 20,
        workflow_state: Optional[str] = None,
        severity: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """List entries with filters."""
        entries = await self.repo.get_multi_with_filters(
            skip=skip,
            limit=limit,
            workflow_state=workflow_state,
            severity=severity,
            created_by=created_by,
        )
        
        filters = {}
        if workflow_state:
            filters["workflow_state"] = workflow_state
        if severity:
            filters["severity"] = severity
        if created_by:
            filters["created_by"] = created_by
            
        total = await self.repo.count(filters)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": entries,
        }

    async def update_entry(self, entry_id: UUID, entry_data: EntryUpdate):
        """Update entry."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        if entry.workflow_state not in ["draft", "in_review"]:
            raise WorkflowError(f"Cannot update entry in {entry.workflow_state} state")

        data_dict = entry_data.model_dump(exclude_unset=True)
        updated = await self.repo.update(entry_id, data_dict)
        full_entry = await self.repo.get_with_relations(entry_id)
        
        # Re-index in Meilisearch
        await self._index_entry(full_entry)
        
        return full_entry

    async def delete_entry(self, entry_id: UUID):
        """Soft delete entry by marking as retired."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        await self.repo.update_workflow_state(entry_id, "retired")
        
        # Remove from search index
        await self._delete_entry_from_index(entry_id)
        
        return True

    async def add_symptom(self, entry_id: UUID, symptom_data: EntrySymptomCreate):
        """Add symptom to entry."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        symptom = await self.repo.add_symptom(entry_id, symptom_data.model_dump())
        return symptom

    async def add_incident(self, entry_id: UUID, incident_data: EntryIncidentCreate):
        """Link incident to entry."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        incident = await self.repo.add_incident(entry_id, incident_data.model_dump())
        return incident

    async def transition_workflow(self, entry_id: UUID, new_state: str, approved_by: Optional[str] = None):
        """Transition entry to new workflow state."""
        entry = await self.repo.get(entry_id)
        if not entry:
            raise NotFoundError(f"Entry {entry_id} not found")

        current_state = entry.workflow_state
        valid_transitions = self.VALID_WORKFLOW_TRANSITIONS.get(current_state, [])

        if new_state not in valid_transitions:
            raise WorkflowError(
                f"Invalid transition from {current_state} to {new_state}. "
                f"Valid transitions: {', '.join(valid_transitions)}"
            )

        return await self.repo.update_workflow_state(entry_id, new_state, approved_by)
