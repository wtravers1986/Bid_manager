"""
API endpoints for AI analysis operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models import SessionSection, ContentConflict
from app.services import OpenAIService
from app.services.vector_store import VectorStore
from app.agents import ContradictionAgent, SummarizationAgent, RankingAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for analysis."""
    section_id: int
    analysis_type: str  # "contradiction", "summarize", "rank"


class ConflictResponse(BaseModel):
    """Response model for detected conflicts."""
    id: int
    conflict_type: str
    description: str
    confidence: float
    severity: str
    is_resolved: bool

    class Config:
        from_attributes = True


@router.post("/section/{section_id}/detect-contradictions")
async def detect_contradictions(
    section_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Detect contradictions between candidate passages in a section.
    """
    logger.info(f"Detecting contradictions in section {section_id}")

    try:
        # Get section
        result = await db.execute(
            select(SessionSection).where(SessionSection.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_id} not found",
            )

        # Get candidates with content
        candidates = []
        for candidate in section.candidates:
            if candidate.chunk:
                candidates.append({
                    "chunk_id": candidate.chunk_id,
                    "content": candidate.chunk.content,
                    "source": candidate.chunk.source_document.filename if candidate.chunk.source_document else "Unknown",
                })

        if len(candidates) < 2:
            return {
                "conflicts": [],
                "message": "Not enough candidates to compare",
            }

        # Run contradiction detection
        openai_service = OpenAIService()
        agent = ContradictionAgent(openai_service)

        result = await agent.execute(
            candidates=candidates,
            section_context=f"{section.section_number} {section.section_title}",
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Contradiction detection failed: {result.error}",
            )

        # Store conflicts in database
        conflicts_data = result.data.get("conflicts", [])
        stored_conflicts = []

        for conflict in conflicts_data:
            # Create conflict record
            db_conflict = ContentConflict(
                section_id=section_id,
                candidate_a_id=conflict.get("candidate_a_id"),
                candidate_b_id=conflict.get("candidate_b_id"),
                conflict_type=conflict.get("conflict_type"),
                conflict_description=conflict.get("description"),
                confidence=conflict.get("confidence"),
                is_resolved=False,
            )

            db.add(db_conflict)
            stored_conflicts.append(db_conflict)

        await db.commit()

        logger.info(f"Detected {len(stored_conflicts)} conflicts in section {section_id}")

        return {
            "section_id": section_id,
            "conflicts_found": len(stored_conflicts),
            "total_comparisons": result.data.get("total_comparisons"),
            "high_severity_count": result.data.get("high_severity_count"),
            "conflicts": conflicts_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting contradictions: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect contradictions",
        )


@router.post("/section/{section_id}/generate-summary")
async def generate_summary(
    section_id: int,
    target_length: str = "medium",
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI summary for a section from its candidates.
    """
    logger.info(f"Generating summary for section {section_id}")

    try:
        # Get section
        result = await db.execute(
            select(SessionSection).where(SessionSection.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_id} not found",
            )

        # Get candidates with content
        candidates = []
        for candidate in section.candidates:
            if candidate.chunk and candidate.chunk.source_document:
                candidates.append({
                    "chunk_id": candidate.chunk_id,
                    "content": candidate.chunk.content,
                    "source": candidate.chunk.source_document.filename,
                    "page_number": candidate.chunk.page_number,
                })

        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No candidates available for summarization",
            )

        # Run summarization
        openai_service = OpenAIService()
        agent = SummarizationAgent(openai_service)

        result = await agent.execute(
            candidates=candidates,
            section_title=section.section_title,
            target_length=target_length,
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summarization failed: {result.error}",
            )

        # Update section with AI draft
        section.ai_draft = result.data.get("summary")
        section.ai_summary = "\n".join(result.data.get("key_points", []))
        section.ai_confidence = result.confidence
        section.status = "ready_for_review"

        await db.commit()

        logger.info(f"Generated summary for section {section_id}")

        return {
            "section_id": section_id,
            "summary": result.data.get("summary"),
            "key_points": result.data.get("key_points"),
            "citations_used": len(result.data.get("citations_map", {})),
            "contradictions_noted": result.data.get("contradictions_noted"),
            "confidence": result.confidence,
            "word_count": result.data.get("word_count"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary",
        )


@router.get("/section/{section_id}/conflicts", response_model=list[ConflictResponse])
async def get_section_conflicts(
    section_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all conflicts for a section.
    """
    try:
        result = await db.execute(
            select(ContentConflict)
            .where(ContentConflict.section_id == section_id)
            .order_by(ContentConflict.confidence.desc())
        )
        conflicts = result.scalars().all()

        return [
            ConflictResponse(
                id=c.id,
                conflict_type=c.conflict_type,
                description=c.conflict_description,
                confidence=c.confidence,
                severity="high",  # TODO: compute from confidence
                is_resolved=c.is_resolved,
            )
            for c in conflicts
        ]

    except Exception as e:
        logger.error(f"Error getting conflicts for section {section_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conflicts",
        )
