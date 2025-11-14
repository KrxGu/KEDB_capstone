"""Solution models: workarounds and resolutions with ordered steps."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SolutionType(str, PyEnum):
    """Type of solution provided."""

    WORKAROUND = "workaround"  # Temporary fix
    RESOLUTION = "resolution"  # Permanent fix


class Solution(Base):
    """A solution (workaround or resolution) for an entry."""

    __tablename__ = "solutions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    solution_type: Mapped[SolutionType] = mapped_column(
        Enum(SolutionType, name="solution_type"),
        nullable=False,
        index=True,
    )
    
    # Metadata
    estimated_time_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    prerequisites: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tracking
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="solutions")
    
    steps: Mapped[List["SolutionStep"]] = relationship(
        "SolutionStep",
        back_populates="solution",
        cascade="all, delete-orphan",
        order_by="SolutionStep.order_index",
    )
    
    embeddings: Mapped[List["SolutionEmbedding"]] = relationship(
        "SolutionEmbedding",
        back_populates="solution",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Solution(id={self.id}, type={self.solution_type}, entry_id={self.entry_id})>"


class SolutionStep(Base):
    """Individual ordered step within a solution."""

    __tablename__ = "solution_steps"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    solution_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("solutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Step content
    action: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[Optional[str]] = mapped_column(Text)
    
    # Command/code to execute (optional)
    command: Mapped[Optional[str]] = mapped_column(Text)
    
    # Rollback information
    rollback_action: Mapped[Optional[str]] = mapped_column(Text)
    rollback_command: Mapped[Optional[str]] = mapped_column(Text)
    
    # Additional metadata (JSON for flexibility)
    step_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    solution: Mapped["Solution"] = relationship("Solution", back_populates="steps")

    __table_args__ = (
        Index("ix_solution_steps_solution_order", "solution_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<SolutionStep(solution_id={self.solution_id}, order={self.order_index})>"


# Forward references
from app.models.embedding import SolutionEmbedding  # noqa: E402
from app.models.entry import Entry  # noqa: E402
