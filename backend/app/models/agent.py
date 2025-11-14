"""Agent models: tracking agent sessions, calls, and policy decisions."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AgentSession(Base):
    """A conversation session with the agent."""

    __tablename__ = "agent_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Context
    incident_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    context: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    calls: Mapped[list["AgentCall"]] = relationship(
        "AgentCall",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AgentSession(id={self.id}, user={self.user_id})>"


class AgentCall(Base):
    """Individual agent API call (suggest or run)."""

    __tablename__ = "agent_calls"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        index=True,
    )
    
    # Call type and tool
    call_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "suggest", "run"
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Input/output
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Performance and cost
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "success", "error", "denied"
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    session: Mapped[Optional["AgentSession"]] = relationship("AgentSession", back_populates="calls")
    
    suggestions: Mapped[list["AgentSuggestion"]] = relationship(
        "AgentSuggestion",
        back_populates="agent_call",
        cascade="all, delete-orphan",
    )
    
    policy_decisions: Mapped[list["PolicyDecision"]] = relationship(
        "PolicyDecision",
        back_populates="agent_call",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agent_calls_session_created", "session_id", "created_at"),
        Index("ix_agent_calls_type_status", "call_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<AgentCall(id={self.id}, type={self.call_type}, status={self.status})>"


class AgentSuggestion(Base):
    """A specific suggestion made by the agent."""

    __tablename__ = "agent_suggestions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_call_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Referenced KEDB content
    entry_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    solution_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    step_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Suggestion content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Citation info (spans in original KEDB content)
    citation_spans: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Confidence
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Rank in the suggestion list
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    agent_call: Mapped["AgentCall"] = relationship("AgentCall", back_populates="suggestions")

    __table_args__ = (
        Index("ix_agent_suggestions_entry", "entry_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentSuggestion(id={self.id}, entry_id={self.entry_id}, rank={self.rank})>"


class PolicyDecisionResult(str, PyEnum):
    """Policy check result."""

    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"


class PolicyDecision(Base):
    """Policy engine decision for an agent action."""

    __tablename__ = "policy_decisions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_call_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Policy details
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    decision: Mapped[PolicyDecisionResult] = mapped_column(
        Enum(PolicyDecisionResult, name="policy_decision_result"),
        nullable=False,
        index=True,
    )
    
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Context evaluated
    evaluated_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Who approved (if REQUIRES_APPROVAL and was approved)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    agent_call: Mapped["AgentCall"] = relationship("AgentCall", back_populates="policy_decisions")

    __table_args__ = (
        Index("ix_policy_decisions_policy_decision", "policy_name", "decision"),
    )

    def __repr__(self) -> str:
        return f"<PolicyDecision(policy={self.policy_name}, decision={self.decision})>"
