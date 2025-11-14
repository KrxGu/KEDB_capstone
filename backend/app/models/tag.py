"""Tag models: categorization and labeling."""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Tag(Base):
    """Reusable tag for categorizing entries."""

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    
    # Optional grouping (e.g., "service", "environment", "component")
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    description: Mapped[Optional[str]] = mapped_column(String(500))
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    entry_tags: Mapped[List["EntryTag"]] = relationship(
        "EntryTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tag(name={self.name}, category={self.category})>"


class EntryTag(Base):
    """Many-to-many relationship between entries and tags."""

    __tablename__ = "entry_tags"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Who added this tag
    added_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="entry_tags")

    __table_args__ = (
        UniqueConstraint("entry_id", "tag_id", name="uq_entry_tag"),
        Index("ix_entry_tags_entry_tag", "entry_id", "tag_id"),
    )

    def __repr__(self) -> str:
        return f"<EntryTag(entry_id={self.entry_id}, tag_id={self.tag_id})>"


# Forward reference
from app.models.entry import Entry  # noqa: E402
