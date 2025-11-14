"""Entry models: main KEDB entries with symptoms and linked incidents."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WorkflowState(str, PyEnum):
    """Entry workflow states."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    RETIRED = "retired"
    MERGED = "merged"


class EntryStatus(str, PyEnum):
    """Entry operational status."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class SeverityLevel(str, PyEnum):
    """Problem severity classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Entry(Base):
    """Main KEDB entry representing a known error/problem."""

    __tablename__ = "entries"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Severity and categorization
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel, name="severity_level"), 
        nullable=False, 
        index=True
    )
    
    # Workflow tracking
    workflow_state: Mapped[WorkflowState] = mapped_column(
        Enum(WorkflowState, name="workflow_state"),
        nullable=False,
        default=WorkflowState.DRAFT,
        index=True,
    )
    status: Mapped[EntryStatus] = mapped_column(
        Enum(EntryStatus, name="entry_status"),
        nullable=False,
        default=EntryStatus.ACTIVE,
        index=True,
    )
    
    # Ownership and attribution
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Merge tracking
    merged_into_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("entries.id", ondelete="SET NULL"),
        index=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    impact_summary: Mapped[Optional[str]] = mapped_column(Text)
    detection_method: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationships
    symptoms: Mapped[List["EntrySymptom"]] = relationship(
        "EntrySymptom",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="EntrySymptom.order_index",
    )
    
    solutions: Mapped[List["Solution"]] = relationship(
        "Solution",
        back_populates="entry",
        cascade="all, delete-orphan",
    )
    
    incidents: Mapped[List["EntryIncident"]] = relationship(
        "EntryIncident",
        back_populates="entry",
        cascade="all, delete-orphan",
    )
    
    tags: Mapped[List["EntryTag"]] = relationship(
        "EntryTag",
        back_populates="entry",
        cascade="all, delete-orphan",
    )
    
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="entry",
        cascade="all, delete-orphan",
    )
    
    embeddings: Mapped[List["EntryEmbedding"]] = relationship(
        "EntryEmbedding",
        back_populates="entry",
        cascade="all, delete-orphan",
    )
    
    merged_into: Mapped[Optional["Entry"]] = relationship(
        "Entry",
        remote_side=[id],
        foreign_keys=[merged_into_id],
    )

    __table_args__ = (
        Index("ix_entries_workflow_severity", "workflow_state", "severity"),
        Index("ix_entries_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Entry(id={self.id}, title={self.title[:50]}, state={self.workflow_state})>"


class EntrySymptom(Base):
    """Observable symptoms/indicators of the problem (ordered)."""

    __tablename__ = "entry_symptoms"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Optional metadata
    symptom_type: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "log_pattern", "metric_spike"
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="symptoms")

    __table_args__ = (
        Index("ix_entry_symptoms_entry_order", "entry_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<EntrySymptom(entry_id={self.entry_id}, order={self.order_index})>"


class EntryIncident(Base):
    """Link between KEDB entries and actual incidents."""

    __tablename__ = "entry_incidents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # External incident reference
    incident_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    incident_source: Mapped[str] = mapped_column(String(100))  # e.g., "pagerduty", "opsgenie"
    incident_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Incident metadata
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="incidents")

    __table_args__ = (
        Index("ix_entry_incidents_incident_id", "incident_id"),
    )

    def __repr__(self) -> str:
        return f"<EntryIncident(incident_id={self.incident_id}, entry_id={self.entry_id})>"


# Forward references for type checking
from app.models.embedding import EntryEmbedding  # noqa: E402
from app.models.review import Review  # noqa: E402
from app.models.solution import Solution  # noqa: E402
from app.models.tag import EntryTag  # noqa: E402
