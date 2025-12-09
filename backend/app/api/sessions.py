"""
API endpoints for cleanup sessions.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models import CleanupSession, SessionStatus
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models for requests/responses
class CreateSessionRequest(BaseModel):
    """Request model for creating a session."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    table_of_contents: dict | None = None
    personas: list[str] | None = None
    scope_criteria: dict | None = None


class SessionResponse(BaseModel):
    """Response model for a session."""
    id: int
    name: str
    description: str | None
    status: str
    total_documents: int
    processed_documents: int
    total_sections: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session."""
    name: str | None = None
    description: str | None = None
    status: SessionStatus | None = None
    table_of_contents: dict | None = None
    personas: list[str] | None = None


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new cleanup session.

    A session represents one execution of the document cleanup process.
    """
    logger.info(f"Creating new session: {request.name}")

    try:
        # Create new session
        session = CleanupSession(
            name=request.name,
            description=request.description,
            status=SessionStatus.CREATED,
            table_of_contents=request.table_of_contents,
            personas=request.personas,
            scope_criteria=request.scope_criteria,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(f"Created session {session.id}")

        return SessionResponse(
            id=session.id,
            name=session.name,
            description=session.description,
            status=session.status.value,
            total_documents=session.total_documents,
            processed_documents=session.processed_documents,
            total_sections=session.total_sections,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    List all cleanup sessions.
    """
    try:
        result = await db.execute(
            select(CleanupSession)
            .order_by(CleanupSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()

        return [
            SessionResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                status=s.status.value,
                total_documents=s.total_documents,
                processed_documents=s.processed_documents,
                total_sections=s.total_sections,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
            )
            for s in sessions
        ]

    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions",
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific session by ID.
    """
    try:
        result = await db.execute(
            select(CleanupSession).where(CleanupSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        return SessionResponse(
            id=session.id,
            name=session.name,
            description=session.description,
            status=session.status.value,
            total_documents=session.total_documents,
            processed_documents=session.processed_documents,
            total_sections=session.total_sections,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session",
        )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    request: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a session.
    """
    try:
        result = await db.execute(
            select(CleanupSession).where(CleanupSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Update fields
        if request.name is not None:
            session.name = request.name
        if request.description is not None:
            session.description = request.description
        if request.status is not None:
            session.status = request.status
        if request.table_of_contents is not None:
            session.table_of_contents = request.table_of_contents
        if request.personas is not None:
            session.personas = request.personas

        await db.commit()
        await db.refresh(session)

        logger.info(f"Updated session {session_id}")

        return SessionResponse(
            id=session.id,
            name=session.name,
            description=session.description,
            status=session.status.value,
            total_documents=session.total_documents,
            processed_documents=session.processed_documents,
            total_sections=session.total_sections,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session",
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a session and all associated data.
    """
    try:
        result = await db.execute(
            select(CleanupSession).where(CleanupSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        await db.delete(session)
        await db.commit()

        logger.info(f"Deleted session {session_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session",
        )
