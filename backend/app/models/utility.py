"""Utility models: prompts, attachments, synonyms."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Prompt(Base):
    """Versioned prompt templates for the agent."""

    __tablename__ = "prompts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    
    # Prompt content
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    user_prompt_template: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # A/B testing flags
    ab_test_group: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_prompts_name_version", "name", "version"),
        Index("ix_prompts_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Prompt(name={self.name}, version={self.version}, active={self.is_active})>"


class Attachment(Base):
    """File attachments for entries (logs, screenshots, etc.)."""

    __tablename__ = "attachments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # What it's attached to
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    # File info
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    
    # Storage location (S3 key, local path, etc.)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Optional metadata
    file_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_attachments_entity", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<Attachment(filename={self.filename}, entity={self.entity_type}:{self.entity_id})>"


class Synonym(Base):
    """Search synonyms for better query matching."""

    __tablename__ = "synonyms"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    term: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    synonyms: Mapped[list] = mapped_column(JSONB, nullable=False)  # Array of synonym strings
    
    # Optional grouping
    category: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Synonym(term={self.term})>"
