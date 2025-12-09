"""
Database models for cleanup sessions.
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
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, IDMixin, UserTrackingMixin


class SessionStatus(str, PyEnum):
    """Status of a cleanup session."""
    CREATED = "created"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class CleanupSession(Base, IDMixin, TimestampMixin, UserTrackingMixin):
    """
    A cleanup session represents one execution of the document cleanup process.

    Process owners create a session, select documents, and work through
    the review process to generate consolidated output documents.
    """
    __tablename__ = "cleanup_sessions"

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(SessionStatus),
        default=SessionStatus.CREATED,
        nullable=False,
        index=True,
    )

    # Configuration
    table_of_contents = Column(JSON, nullable=True)  # ToC structure as JSON
    personas = Column(JSON, nullable=True)  # List of target personas
    scope_criteria = Column(JSON, nullable=True)  # Document selection criteria

    # Processing metadata
    total_documents = Column(Integer, default=0)
    processed_documents = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    total_sections = Column(Integer, default=0)

    # Output configuration
    output_format = Column(String(50), default="docx")  # docx, pdf
    output_template = Column(String(255), nullable=True)  # Path to template

    # Relationships
    source_documents = relationship(
        "SourceDocument",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    sections = relationship(
        "SessionSection",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    output_documents = relationship(
        "OutputDocument",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CleanupSession(id={self.id}, name='{self.name}', status='{self.status}')>"


class SourceDocument(Base, IDMixin, TimestampMixin):
    """
    A source document that is part of a cleanup session.
    These are the ~207 original documents to be analyzed.
    """
    __tablename__ = "source_documents"

    # Session relationship
    session_id = Column(Integer, ForeignKey("cleanup_sessions.id"), nullable=False)
    session = relationship("CleanupSession", back_populates="source_documents")

    # Document identification
    filename = Column(String(512), nullable=False)
    original_path = Column(String(1024), nullable=True)  # SharePoint path
    blob_path = Column(String(1024), nullable=True)  # Azure Blob path
    document_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash

    # Metadata
    file_type = Column(String(50), nullable=False)  # pdf, docx, etc.
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    document_date = Column(String(50), nullable=True)  # Date from document metadata
    document_version = Column(String(50), nullable=True)
    document_owner = Column(String(255), nullable=True)

    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    # Extracted content
    extracted_text = Column(Text, nullable=True)  # Full text if needed
    metadata_json = Column(JSON, nullable=True)  # Additional metadata

    # Relationships
    chunks = relationship(
        "DocumentChunk",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    figures = relationship(
        "DocumentFigure",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<SourceDocument(id={self.id}, filename='{self.filename}')>"


class DocumentChunk(Base, IDMixin, TimestampMixin):
    """
    A chunk of text extracted from a source document.
    Chunks are created during document parsing and used for vector search.
    """
    __tablename__ = "document_chunks"

    # Relationships
    source_document_id = Column(
        Integer,
        ForeignKey("source_documents.id"),
        nullable=False,
    )
    source_document = relationship("SourceDocument", back_populates="chunks")

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(512), nullable=True)

    # Vector search
    vector_id = Column(String(255), nullable=True, index=True)  # ID in vector store
    embedding_model = Column(String(100), nullable=True)

    # Chunk metadata
    token_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, doc={self.source_document_id}, idx={self.chunk_index})>"


class DocumentFigure(Base, IDMixin, TimestampMixin):
    """
    A figure/image extracted from a source document.
    """
    __tablename__ = "document_figures"

    # Relationships
    source_document_id = Column(
        Integer,
        ForeignKey("source_documents.id"),
        nullable=False,
    )
    source_document = relationship("SourceDocument", back_populates="figures")

    # Figure identification
    figure_index = Column(Integer, nullable=False)  # Order in document
    page_number = Column(Integer, nullable=True)
    caption = Column(Text, nullable=True)
    figure_number = Column(String(50), nullable=True)  # e.g., "Figure 3.2"

    # Storage
    blob_path = Column(String(1024), nullable=True)  # Path to extracted image
    image_format = Column(String(20), nullable=True)  # png, jpg, etc.

    # Metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    ocr_text = Column(Text, nullable=True)  # Text from OCR if applied

    def __repr__(self) -> str:
        return f"<DocumentFigure(id={self.id}, doc={self.source_document_id}, idx={self.figure_index})>"
