"""Models package - import all models for Alembic autogenerate."""
from app.models.base import Base

# Import all models so Alembic can detect them
from app.models.agent import AgentCall, AgentSession, AgentSuggestion, PolicyDecision
from app.models.audit import AuditLog, SuggestionEvent
from app.models.embedding import EntryEmbedding, SolutionEmbedding
from app.models.entry import Entry, EntryIncident, EntrySymptom
from app.models.review import Review, ReviewParticipant
from app.models.solution import Solution, SolutionStep
from app.models.tag import EntryTag, Tag
from app.models.utility import Attachment, Prompt, Synonym

__all__ = [
    "Base",
    # Entry models
    "Entry",
    "EntrySymptom",
    "EntryIncident",
    # Solution models
    "Solution",
    "SolutionStep",
    # Tag models
    "Tag",
    "EntryTag",
    # Review models
    "Review",
    "ReviewParticipant",
    # Audit models
    "AuditLog",
    "SuggestionEvent",
    # Embedding models
    "EntryEmbedding",
    "SolutionEmbedding",
    # Agent models
    "AgentSession",
    "AgentCall",
    "AgentSuggestion",
    "PolicyDecision",
    # Utility models
    "Prompt",
    "Attachment",
    "Synonym",
]
