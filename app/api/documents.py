"""
API endpoints for document management.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models import SourceDocument, CleanupSession
from app.parsers import ParserFactory
from app.services import StorageService, OpenAIService
from app.services.indexing_service import IndexingService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class DocumentResponse(BaseModel):
    """Response model for a document."""
    id: int
    filename: str
    file_type: str
    file_size_bytes: int | None
    page_count: int | None
    is_processed: bool
    created_at: str

    class Config:
        from_attributes = True


@router.post("/upload/{session_id}", status_code=status.HTTP_201_CREATED)
async def upload_document(
    session_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a source document to a session.

    This endpoint:
    1. Validates the file
    2. Saves to local filesystem (data/source/session_{session_id}/)
    3. Creates a database record
    4. Triggers parsing (async)
    """
    logger.info(f"Uploading document {file.filename} to session {session_id}")

    # Verify session exists
    result = await db.execute(
        select(CleanupSession).where(CleanupSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Validate file type
    parser_factory = ParserFactory()
    if not parser_factory.supports_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {parser_factory.supported_extensions()}",
        )

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Check file size
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
            )

        # Save to local filesystem
        storage_service = StorageService()
        subdirectory = f"session_{session_id}"
        file_path = await storage_service.upload_file(
            file_content,
            file.filename,
            subdirectory=subdirectory,
            content_type=file.content_type,
        )

        # Create document record
        document = SourceDocument(
            session_id=session_id,
            filename=file.filename,
            blob_path=file_path,  # Keep field name for compatibility
            file_type=file.filename.split('.')[-1].lower(),
            file_size_bytes=file_size,
            is_processed=False,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        logger.info(f"Created document {document.id} in session {session_id}")

        # TODO: Trigger async parsing task with Celery

        return {
            "id": document.id,
            "filename": document.filename,
            "status": "uploaded",
            "message": "Document uploaded successfully. Processing will begin shortly.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get("/session/{session_id}", response_model=list[DocumentResponse])
async def list_session_documents(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    List all documents in a session.
    """
    try:
        result = await db.execute(
            select(SourceDocument)
            .where(SourceDocument.session_id == session_id)
            .order_by(SourceDocument.created_at.desc())
        )
        documents = result.scalars().all()

        return [
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                file_size_bytes=d.file_size_bytes,
                page_count=d.page_count,
                is_processed=d.is_processed,
                created_at=d.created_at.isoformat(),
            )
            for d in documents
        ]

    except Exception as e:
        logger.error(f"Error listing documents for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific document.
    """
    try:
        result = await db.execute(
            select(SourceDocument).where(SourceDocument.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size_bytes=document.file_size_bytes,
            page_count=document.page_count,
            is_processed=document.is_processed,
            created_at=document.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.post("/scan-data-folder/{session_id}", status_code=status.HTTP_200_OK)
async def scan_data_folder(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Scan the data folder and import all supported documents into the session.
    
    This endpoint:
    1. Scans the data folder for PDF/DOCX files
    2. Creates database records for each file
    3. Returns list of imported documents
    """
    logger.info(f"Scanning data folder for session {session_id}")

    # Verify session exists
    result = await db.execute(
        select(CleanupSession).where(CleanupSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    try:
        storage_service = StorageService()
        parser_factory = ParserFactory()
        
        # List all files directly in data folder root (not in subdirectories)
        # We'll scan the data_dir directly
        data_dir = storage_service.data_dir
        all_files = []
        
        if data_dir.exists():
            for file_path in data_dir.iterdir():
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in [".pdf", ".docx", ".doc"]:
                        stat = file_path.stat()
                        all_files.append({
                            "name": file_path.name,
                            "path": file_path.name,  # Just filename for root level
                            "size": stat.st_size,
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "extension": ext,
                        })

        imported_documents = []
        skipped_documents = []

        for file_info in all_files:
            file_path = file_info["path"]
            filename = file_info["name"]
            
            # Check if file is already in database for this session
            existing = await db.execute(
                select(SourceDocument).where(
                    SourceDocument.session_id == session_id,
                    SourceDocument.filename == filename
                )
            )
            if existing.scalar_one_or_none():
                skipped_documents.append({
                    "filename": filename,
                    "reason": "Already imported"
                })
                continue

            # Get full path (file_path is just filename for root level files)
            full_path = storage_service.data_dir / file_info["name"]
            
            # Read file
            try:
                file_content = full_path.read_bytes()
                file_size = file_info["size"]
            except Exception as e:
                logger.error(f"Error reading file {full_path}: {e}")
                skipped_documents.append({
                    "filename": filename,
                    "reason": f"Read error: {str(e)}"
                })
                continue

            # Create document record
            document = SourceDocument(
                session_id=session_id,
                filename=filename,
                blob_path=str(full_path),  # Store full path
                file_type=file_info["extension"].lstrip("."),
                file_size_bytes=file_size,
                is_processed=False,
            )

            db.add(document)
            imported_documents.append({
                "filename": filename,
                "file_type": document.file_type,
                "size": file_size,
            })

        await db.commit()

        logger.info(
            f"Imported {len(imported_documents)} documents, "
            f"skipped {len(skipped_documents)} for session {session_id}"
        )

        return {
            "session_id": session_id,
            "imported_count": len(imported_documents),
            "skipped_count": len(skipped_documents),
            "imported_documents": imported_documents,
            "skipped_documents": skipped_documents,
        }

    except Exception as e:
        logger.error(f"Error scanning data folder: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan data folder: {str(e)}",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document and its associated data.
    """
    try:
        result = await db.execute(
            select(SourceDocument).where(SourceDocument.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Delete from local filesystem
        if document.blob_path:
            storage_service = StorageService()
            # blob_path now contains the full file path
            await storage_service.delete_file(document.blob_path)

        # Delete from database
        await db.delete(document)
        await db.commit()

        logger.info(f"Deleted document {document_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.post("/index-data-folder", status_code=status.HTTP_200_OK)
async def index_data_folder(
    session_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Process and index all documents from the data folder into local HNSW vector store.
    
    This endpoint:
    1. Scans the data folder for PDF/DOCX files
    2. Parses each document
    3. Chunks the text
    4. Generates embeddings
    5. Indexes all chunks in local HNSW vector store
    
    Args:
        session_id: Optional session ID to associate documents with
    """
    logger.info("Starting indexing process for data folder")

    try:
        indexing_service = IndexingService()

        # Process and index documents
        result = await indexing_service.process_and_index_documents(
            session_id=session_id
        )

        return result

    except Exception as e:
        logger.error(f"Error indexing data folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index data folder: {str(e)}",
        )


@router.get("/index-schema", status_code=status.HTTP_200_OK)
async def get_index_schema():
    """
    Get the local HNSW vector store schema as JSON.
    
    Returns the schema definition and statistics for the vector store.
    """
    try:
        indexing_service = IndexingService()
        schema = await indexing_service.generate_index_schema_json()
        return schema

    except Exception as e:
        logger.error(f"Error getting index schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index schema: {str(e)}",
        )
