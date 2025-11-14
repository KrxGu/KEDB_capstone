"""Review models: approval workflow and review process."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReviewStatus(str, PyEnum):
    """Review approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ParticipantRole(str, PyEnum):
    """Role in the review process."""

    LEAD = "lead"  # Primary reviewer
    REVIEWER = "reviewer"  # Additional reviewer
    OBSERVER = "observer"  # Notified but not required to approve


class Review(Base):
    """Review session for an entry before publication."""

    __tablename__ = "reviews"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entry_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        nullable=False,
        default=ReviewStatus.PENDING,
        index=True,
    )
    
    # Review content
    comments: Mapped[Optional[str]] = mapped_column(Text)
    rca_text: Mapped[Optional[str]] = mapped_column(Text)  # Root cause analysis
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    entry: Mapped["Entry"] = relationship("Entry", back_populates="reviews")
    
    participants: Mapped[List["ReviewParticipant"]] = relationship(
        "ReviewParticipant",
        back_populates="review",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, entry_id={self.entry_id}, status={self.status})>"


class ReviewParticipant(Base):
    """Participant in a review session."""

    __tablename__ = "review_participants"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    review_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(ParticipantRole, name="participant_role"),
        nullable=False,
    )
    
    # Approval tracking
    approved: Mapped[Optional[bool]] = mapped_column(default=None)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="participants")

    __table_args__ = (
        Index("ix_review_participants_review_user", "review_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<ReviewParticipant(review_id={self.review_id}, user={self.user_id}, role={self.role})>"


# Forward reference
from app.models.entry import Entry  # noqa: E402
