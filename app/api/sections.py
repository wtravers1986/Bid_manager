"""
API endpoints for section management and review.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models import SessionSection, SectionStatus, SectionCandidate, ReviewDecision
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SectionResponse(BaseModel):
    """Response model for a section."""
    id: int
    section_number: str
    section_title: str
    status: str
    ai_draft: str | None
    ai_summary: str | None
    ai_confidence: float | None
    final_content: str | None
    created_at: str

    class Config:
        from_attributes = True


class UpdateSectionRequest(BaseModel):
    """Request model for updating a section."""
    status: SectionStatus | None = None
    reviewer_notes: str | None = None
    final_content: str | None = None


class CandidateResponse(BaseModel):
    """Response model for a section candidate."""
    id: int
    chunk_id: int
    relevance_score: float
    rank: int
    is_selected: bool
    reviewer_decision: str
    content: str | None = None

    class Config:
        from_attributes = True


class ReviewCandidateRequest(BaseModel):
    """Request model for reviewing a candidate."""
    decision: ReviewDecision
    reviewer_notes: str | None = None


@router.get("/session/{session_id}", response_model=list[SectionResponse])
async def list_session_sections(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    List all sections in a session.
    """
    try:
        result = await db.execute(
            select(SessionSection)
            .where(SessionSection.session_id == session_id)
            .order_by(SessionSection.section_number)
        )
        sections = result.scalars().all()

        return [
            SectionResponse(
                id=s.id,
                section_number=s.section_number,
                section_title=s.section_title,
                status=s.status.value,
                ai_draft=s.ai_draft,
                ai_summary=s.ai_summary,
                ai_confidence=s.ai_confidence,
                final_content=s.final_content,
                created_at=s.created_at.isoformat(),
            )
            for s in sections
        ]

    except Exception as e:
        logger.error(f"Error listing sections for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sections",
        )


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific section.
    """
    try:
        result = await db.execute(
            select(SessionSection).where(SessionSection.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_id} not found",
            )

        return SectionResponse(
            id=section.id,
            section_number=section.section_number,
            section_title=section.section_title,
            status=section.status.value,
            ai_draft=section.ai_draft,
            ai_summary=section.ai_summary,
            ai_confidence=section.ai_confidence,
            final_content=section.final_content,
            created_at=section.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting section {section_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get section",
        )


@router.patch("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    request: UpdateSectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a section (typically by reviewer).
    """
    try:
        result = await db.execute(
            select(SessionSection).where(SessionSection.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_id} not found",
            )

        # Update fields
        if request.status is not None:
            section.status = request.status
        if request.reviewer_notes is not None:
            section.reviewer_notes = request.reviewer_notes
        if request.final_content is not None:
            section.final_content = request.final_content

        await db.commit()
        await db.refresh(section)

        logger.info(f"Updated section {section_id}")

        return SectionResponse(
            id=section.id,
            section_number=section.section_number,
            section_title=section.section_title,
            status=section.status.value,
            ai_draft=section.ai_draft,
            ai_summary=section.ai_summary,
            ai_confidence=section.ai_confidence,
            final_content=section.final_content,
            created_at=section.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating section {section_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update section",
        )


@router.get("/{section_id}/candidates", response_model=list[CandidateResponse])
async def get_section_candidates(
    section_id: int,
    include_content: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all candidate passages for a section.
    """
    try:
        result = await db.execute(
            select(SectionCandidate)
            .where(SectionCandidate.section_id == section_id)
            .order_by(SectionCandidate.rank)
        )
        candidates = result.scalars().all()

        response = []
        for c in candidates:
            # Get chunk content if requested
            content = None
            if include_content and c.chunk:
                content = c.chunk.content

            response.append(
                CandidateResponse(
                    id=c.id,
                    chunk_id=c.chunk_id,
                    relevance_score=c.relevance_score,
                    rank=c.rank,
                    is_selected=c.is_selected,
                    reviewer_decision=c.reviewer_decision.value,
                    content=content,
                )
            )

        return response

    except Exception as e:
        logger.error(f"Error getting candidates for section {section_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get section candidates",
        )


@router.patch(
    "/{section_id}/candidates/{candidate_id}",
    response_model=CandidateResponse,
)
async def review_candidate(
    section_id: int,
    candidate_id: int,
    request: ReviewCandidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Review a candidate passage (accept/reject/modify).
    """
    try:
        result = await db.execute(
            select(SectionCandidate)
            .where(
                SectionCandidate.id == candidate_id,
                SectionCandidate.section_id == section_id,
            )
        )
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found in section {section_id}",
            )

        # Update review decision
        candidate.reviewer_decision = request.decision
        candidate.reviewer_notes = request.reviewer_notes

        # If accepted, mark as selected
        if request.decision == ReviewDecision.ACCEPT:
            candidate.is_selected = True
        elif request.decision == ReviewDecision.REJECT:
            candidate.is_selected = False

        await db.commit()
        await db.refresh(candidate)

        logger.info(
            f"Reviewed candidate {candidate_id} in section {section_id}: "
            f"{request.decision.value}"
        )

        return CandidateResponse(
            id=candidate.id,
            chunk_id=candidate.chunk_id,
            relevance_score=candidate.relevance_score,
            rank=candidate.rank,
            is_selected=candidate.is_selected,
            reviewer_decision=candidate.reviewer_decision.value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing candidate {candidate_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review candidate",
        )
