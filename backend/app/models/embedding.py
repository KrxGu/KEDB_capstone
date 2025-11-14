"""Embedding models: vector representations for semantic search."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class EntryEmbedding(Base):
    """Vector embedding for an entry (title + description + symptoms)."""

    __tablename__ = "entry_embeddings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Embedding metadata
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # The actual vector (pgvector type)
    # Using 3072 for text-embedding-3-large
    embedding: Mapped[Optional[list]] = mapped_column(Vector(3072))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<EntryEmbedding(entry_id={self.entry_id}, model={self.model_name})>"


class SolutionEmbedding(Base):
    """Vector embedding for a solution (title + description + steps)."""

    __tablename__ = "solution_embeddings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    solution_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("solutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Embedding metadata
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # The actual vector
    embedding: Mapped[Optional[list]] = mapped_column(Vector(3072))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    solution: Mapped["Solution"] = relationship("Solution", back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<SolutionEmbedding(solution_id={self.solution_id}, model={self.model_name})>"


# Forward references
from app.models.entry import Entry  # noqa: E402
from app.models.solution import Solution  # noqa: E402
