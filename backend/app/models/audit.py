"""Audit and analytics models: tracking changes and suggestions."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Audit trail for all mutations in the system."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # What was changed
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Field-level diffs (JSON: {field: {old: x, new: y}})
    diff_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Who and when
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_user", "created_at", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(entity={self.entity_type}:{self.entity_id}, action={self.action})>"


class SuggestionEvent(Base):
    """Track AI suggestions and their outcomes."""

    __tablename__ = "suggestion_events"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # What was suggested
    query: Mapped[str] = mapped_column(Text, nullable=False)
    top_entry_ids: Mapped[list] = mapped_column(JSONB, nullable=False)  # Array of entry IDs
    
    # User action
    action: Mapped[Optional[str]] = mapped_column(
        String(50), 
        index=True
    )  # "viewed", "clicked", "applied", "rejected", "dismissed"
    
    # Feedback
    feedback_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 rating
    feedback_text: Mapped[Optional[str]] = mapped_column(Text)
    
    # Score breakdown
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB)  # {bm25, vector, reranker, final}
    
    # Source context
    source_context: Mapped[Optional[dict]] = mapped_column(JSONB)  # Incident details, service, etc.
    
    # Who and when
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Performance
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_suggestion_events_action_created", "action", "created_at"),
        Index("ix_suggestion_events_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SuggestionEvent(id={self.id}, action={self.action})>"
