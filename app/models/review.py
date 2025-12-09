"""
Database models for the review process.
"""
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    JSON,
    ForeignKey,
    Boolean,
    Float,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, IDMixin, UserTrackingMixin


class SectionStatus(str, PyEnum):
    """Status of a section in the review process."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewDecision(str, PyEnum):
    """Decision made by reviewer on a draft."""
    PENDING = "pending"
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"


class SessionSection(Base, IDMixin, TimestampMixin, UserTrackingMixin):
    """
    A section within a cleanup session, based on the Table of Contents.
    Each section goes through AI analysis and human review.
    """
    __tablename__ = "session_sections"

    # Session relationship
    session_id = Column(Integer, ForeignKey("cleanup_sessions.id"), nullable=False)
    session = relationship("CleanupSession", back_populates="sections")

    # Section identification (from ToC)
    section_number = Column(String(50), nullable=False)  # e.g., "3.2.1"
    section_title = Column(String(512), nullable=False)
    section_level = Column(Integer, nullable=False)  # Depth in ToC
    parent_section_id = Column(Integer, ForeignKey("session_sections.id"), nullable=True)

    # Status
    status = Column(
        Enum(SectionStatus),
        default=SectionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # AI-generated content
    ai_draft = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)  # 0.0 - 1.0

    # Review process
    reviewer_notes = Column(Text, nullable=True)
    final_content = Column(Text, nullable=True)

    # Relationships
    parent_section = relationship(
        "SessionSection",
        remote_side=lambda: SessionSection.id,
        backref="child_sections",
    )
    candidates = relationship(
        "SectionCandidate",
        back_populates="section",
        cascade="all, delete-orphan",
    )
    conflicts = relationship(
        "ContentConflict",
        back_populates="section",
        cascade="all, delete-orphan",
    )
    figure_suggestions = relationship(
        "FigureSuggestion",
        back_populates="section",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<SessionSection(id={self.id}, number='{self.section_number}', title='{self.section_title}')>"


class SectionCandidate(Base, IDMixin, TimestampMixin):
    """
    A candidate text passage for a section, retrieved from source documents.
    """
    __tablename__ = "section_candidates"

    # Section relationship
    section_id = Column(Integer, ForeignKey("session_sections.id"), nullable=False)
    section = relationship("SessionSection", back_populates="candidates")

    # Source chunk
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False)
    chunk = relationship("DocumentChunk")

    # Relevance scoring
    relevance_score = Column(Float, nullable=False)  # From vector search
    rank = Column(Integer, nullable=False)  # Ranking within section

    # Review
    is_selected = Column(Boolean, default=False)  # Selected by reviewer
    reviewer_decision = Column(
        Enum(ReviewDecision),
        default=ReviewDecision.PENDING,
        nullable=False,
    )
    reviewer_notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SectionCandidate(id={self.id}, section={self.section_id}, rank={self.rank})>"


class ContentConflict(Base, IDMixin, TimestampMixin):
    """
    A detected conflict or contradiction between candidate passages.
    """
    __tablename__ = "content_conflicts"

    # Section relationship
    section_id = Column(Integer, ForeignKey("session_sections.id"), nullable=False)
    section = relationship("SessionSection", back_populates="conflicts")

    # Conflicting candidates
    candidate_a_id = Column(
        Integer,
        ForeignKey("section_candidates.id"),
        nullable=False,
    )
    candidate_b_id = Column(
        Integer,
        ForeignKey("section_candidates.id"),
        nullable=False,
    )
    candidate_a = relationship(
        "SectionCandidate",
        foreign_keys=[candidate_a_id],
    )
    candidate_b = relationship(
        "SectionCandidate",
        foreign_keys=[candidate_b_id],
    )

    # Conflict details
    conflict_type = Column(String(100), nullable=False)  # contradiction, overlap, etc.
    conflict_description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # AI confidence in conflict detection

    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ContentConflict(id={self.id}, type='{self.conflict_type}', resolved={self.is_resolved})>"


class FigureSuggestion(Base, IDMixin, TimestampMixin):
    """
    An AI-suggested figure to include in a section.
    """
    __tablename__ = "figure_suggestions"

    # Section relationship
    section_id = Column(Integer, ForeignKey("session_sections.id"), nullable=False)
    section = relationship("SessionSection", back_populates="figure_suggestions")

    # Figure reference
    figure_id = Column(Integer, ForeignKey("document_figures.id"), nullable=False)
    figure = relationship("DocumentFigure")

    # Suggestion details
    relevance_score = Column(Float, nullable=False)
    suggested_caption = Column(Text, nullable=True)
    suggested_placement = Column(String(50), nullable=True)  # before, after, inline

    # Review
    is_approved = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=False)  # Marked as required by reviewer
    reviewer_decision = Column(
        Enum(ReviewDecision),
        default=ReviewDecision.PENDING,
        nullable=False,
    )
    final_caption = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<FigureSuggestion(id={self.id}, section={self.section_id}, approved={self.is_approved})>"


class OutputDocument(Base, IDMixin, TimestampMixin, UserTrackingMixin):
    """
    A generated output document (one of the ~3-5 consolidated procedures).
    """
    __tablename__ = "output_documents"

    # Session relationship
    session_id = Column(Integer, ForeignKey("cleanup_sessions.id"), nullable=False)
    session = relationship("CleanupSession", back_populates="output_documents")

    # Document identification
    title = Column(String(512), nullable=False)
    document_type = Column(String(100), nullable=True)  # procedure, guideline, etc.
    target_persona = Column(String(100), nullable=True)  # crane operator, etc.
    version = Column(String(50), default="1.0")

    # Content
    content_json = Column(JSON, nullable=True)  # Structured content
    is_finalized = Column(Boolean, default=False)

    # Output files
    docx_path = Column(String(1024), nullable=True)
    pdf_path = Column(String(1024), nullable=True)

    # Metadata
    changelog = Column(JSON, nullable=True)  # Version history
    approval_status = Column(String(50), default="draft")
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(String(50), nullable=True)

    # Traceability
    source_document_ids = Column(JSON, nullable=True)  # List of source doc IDs used
    section_ids = Column(JSON, nullable=True)  # List of session section IDs

    def __repr__(self) -> str:
        return f"<OutputDocument(id={self.id}, title='{self.title}', version='{self.version}')>"
