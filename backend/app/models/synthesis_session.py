"""
Database models for document synthesis sessions.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, IDMixin, UserTrackingMixin


class SynthesisSession(Base, IDMixin, TimestampMixin, UserTrackingMixin):
    """
    A synthesis session for creating unified documents from multiple sources.
    """
    __tablename__ = "synthesis_sessions"

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="created", nullable=False, index=True)  # created, analyzing, inventory_ready, reviewing, completed

    # Source documents
    source_filenames = Column(JSON, nullable=False)  # List of filenames to synthesize

    # Structure analysis
    document_structures = Column(JSON, nullable=True)  # Analysis results
    inventory_table = Column(JSON, nullable=True)  # Final table of contents

    # User selections
    selected_paragraphs = Column(JSON, nullable=True)  # {section_title: [paragraph_ids]}

    # Generated document
    synthesis_document = Column(Text, nullable=True)  # Final markdown document
    document_path = Column(String(1024), nullable=True)  # Path to generated file

    # Relationships
    paragraphs = relationship(
        "SynthesisParagraph",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<SynthesisSession(id={self.id}, name='{self.name}', status='{self.status}')>"


class SynthesisParagraph(Base, IDMixin, TimestampMixin):
    """
    A paragraph candidate for a synthesis section.
    """
    __tablename__ = "synthesis_paragraphs"

    # Session relationship
    session_id = Column(Integer, ForeignKey("synthesis_sessions.id"), nullable=False)
    session = relationship("SynthesisSession", back_populates="paragraphs")

    # Section information
    section_title = Column(String(512), nullable=False, index=True)
    section_order = Column(Integer, nullable=False)

    # Paragraph content
    paragraph_id = Column(String(255), nullable=False)  # ID from vector store
    content = Column(Text, nullable=False)
    filename = Column(String(512), nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=True)

    # Relevance metrics
    score = Column(String(50), nullable=True)  # Relevance score
    distance = Column(String(50), nullable=True)  # Vector distance

    # User decision
    is_selected = Column(Boolean, default=False, nullable=False)
    user_notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SynthesisParagraph(id={self.id}, section='{self.section_title}', selected={self.is_selected})>"

