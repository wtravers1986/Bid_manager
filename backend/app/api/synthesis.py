"""
API endpoints for document synthesis.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.models.synthesis_session import SynthesisSession, SynthesisParagraph
from app.services.synthesis_service import SynthesisService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class CreateSynthesisSessionRequest(BaseModel):
    """Request to create a synthesis session."""
    name: str
    description: Optional[str] = None
    source_filenames: List[str]


class SynthesisSessionResponse(BaseModel):
    """Response model for synthesis session."""
    id: int
    name: str
    description: Optional[str]
    status: str
    source_filenames: List[str]
    inventory_table: Optional[List[Dict]] = None
    created_at: str

    class Config:
        from_attributes = True


class AnalyzeStructuresRequest(BaseModel):
    """Request to analyze document structures."""
    filenames: List[str]


class UpdateInventoryTableRequest(BaseModel):
    """Request to update inventory table."""
    inventory_table: List[Dict[str, Any]]


class GetParagraphsRequest(BaseModel):
    """Request to get paragraphs for a section."""
    section_title: str
    top_k: int = 10


class SelectParagraphsRequest(BaseModel):
    """Request to select paragraphs for sections."""
    selected_paragraphs: Dict[str, List[str]]  # section_title -> [paragraph_ids]


@router.post("/sessions", response_model=SynthesisSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_synthesis_session(
    request: CreateSynthesisSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new synthesis session."""
    logger.info(f"Creating synthesis session: {request.name}")

    session = SynthesisSession(
        name=request.name,
        description=request.description,
        source_filenames=request.source_filenames,
        status="created"
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SynthesisSessionResponse(
        id=session.id,
        name=session.name,
        description=session.description,
        status=session.status,
        source_filenames=session.source_filenames,
        inventory_table=session.inventory_table,
        created_at=session.created_at.isoformat() if session.created_at else ""
    )


@router.get("/sessions/{session_id}", response_model=SynthesisSessionResponse)
async def get_synthesis_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a synthesis session by ID."""
    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    return SynthesisSessionResponse(
        id=session.id,
        name=session.name,
        description=session.description,
        status=session.status,
        source_filenames=session.source_filenames,
        inventory_table=session.inventory_table,
        created_at=session.created_at.isoformat() if session.created_at else ""
    )


@router.post("/sessions/{session_id}/analyze-structures")
async def analyze_document_structures(
    session_id: int,
    request: AnalyzeStructuresRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze document structures and generate inventory table."""
    logger.info(f"Analyzing structures for session {session_id}")

    # Get session
    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    try:
        # Update status
        session.status = "analyzing"
        await db.commit()

        # Analyze structures
        synthesis_service = SynthesisService()
        analysis_result = await synthesis_service.analyze_document_structures(
            request.filenames
        )

        # Update session with results
        session.document_structures = analysis_result.get('document_structures')
        session.inventory_table = analysis_result.get('common_structure', {}).get('inventory_table')
        session.status = "inventory_ready"
        await db.commit()

        return {
            "success": True,
            "message": "Structure analysis completed",
            "analysis": analysis_result
        }

    except Exception as e:
        logger.error(f"Error analyzing structures: {e}")
        session.status = "created"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze structures: {str(e)}"
        )


@router.put("/sessions/{session_id}/inventory-table")
async def update_inventory_table(
    session_id: int,
    request: UpdateInventoryTableRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update the inventory table for a synthesis session."""
    logger.info(f"Updating inventory table for session {session_id}")

    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    session.inventory_table = request.inventory_table
    await db.commit()

    return {
        "success": True,
        "message": "Inventory table updated",
        "inventory_table": session.inventory_table
    }


@router.post("/sessions/{session_id}/paragraphs")
async def get_paragraphs_for_section(
    session_id: int,
    request: GetParagraphsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get relevant paragraphs for a section."""
    logger.info(f"Getting paragraphs for section: {request.section_title}")

    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    try:
        # Get already used paragraph IDs to avoid duplicates
        used_paragraph_ids = set()
        if session.selected_paragraphs:
            # Collect all used paragraph IDs from all sections
            for section_paras in session.selected_paragraphs.values():
                if isinstance(section_paras, list):
                    used_paragraph_ids.update(section_paras)
        
        synthesis_service = SynthesisService()
        paragraphs = await synthesis_service.find_paragraphs_for_section(
            section_title=request.section_title,
            filenames=session.source_filenames,
            top_k=request.top_k,
            used_paragraph_ids=used_paragraph_ids
        )

        return {
            "success": True,
            "section_title": request.section_title,
            "paragraphs": paragraphs,
            "count": len(paragraphs)
        }

    except Exception as e:
        logger.error(f"Error getting paragraphs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get paragraphs: {str(e)}"
        )


@router.post("/sessions/{session_id}/select-paragraphs")
async def select_paragraphs(
    session_id: int,
    request: SelectParagraphsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save user's paragraph selections."""
    logger.info(f"Saving paragraph selections for session {session_id}")

    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    session.selected_paragraphs = request.selected_paragraphs
    session.status = "reviewing"
    await db.commit()

    return {
        "success": True,
        "message": "Paragraph selections saved",
        "selected_paragraphs": session.selected_paragraphs
    }


@router.post("/sessions/{session_id}/generate-document")
async def generate_synthesis_document(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate the final synthesis document."""
    logger.info(f"Generating synthesis document for session {session_id}")

    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    if not session.inventory_table:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory table not set"
        )

    if not session.selected_paragraphs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No paragraphs selected"
        )

    try:
        synthesis_service = SynthesisService()
        document_bytes = await synthesis_service.generate_synthesis_document(
            inventory_table=session.inventory_table,
            selected_paragraphs=session.selected_paragraphs,
            filenames=session.source_filenames
        )

        # Save document path (store bytes in file system or database)
        from pathlib import Path
        from app.core.config import settings
        import base64
        
        data_dir = Path(settings.data_directory)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save DOCX file
        doc_filename = f"synthesis_session_{session_id}.docx"
        doc_path = data_dir / doc_filename
        doc_path.write_bytes(document_bytes)
        
        # Store as base64 for API response (or just store path)
        document_base64 = base64.b64encode(document_bytes).decode('utf-8')
        
        # Save document info
        session.synthesis_document = document_base64  # Store base64 for now
        session.document_path = str(doc_path)
        session.status = "completed"
        await db.commit()

        return {
            "success": True,
            "message": "Synthesis document generated",
            "document_base64": document_base64,
            "document_path": str(doc_path),
            "filename": doc_filename,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error generating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


@router.get("/sessions/{session_id}/document")
async def get_synthesis_document(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the generated synthesis document as DOCX file."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    result = await db.execute(
        select(SynthesisSession).where(SynthesisSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis session {session_id} not found"
        )

    if not session.document_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthesis document not yet generated"
        )

    doc_path = Path(session.document_path)
    if not doc_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found"
        )

    return FileResponse(
        path=str(doc_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=doc_path.name
    )

