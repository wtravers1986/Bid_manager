"""
API endpoints for vector search operations.
"""
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.openai_service import OpenAIService
from app.services.vector_store import VectorStore
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for vector search."""
    query: str
    top_k: int = 10
    filters: Optional[dict] = None


class SearchResult(BaseModel):
    """Response model for a search result."""
    id: str
    content: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_index: Optional[int] = None
    score: float
    distance: float


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    results: List[SearchResult]
    total_results: int


@router.post("/search", response_model=SearchResponse)
async def vector_search(request: SearchRequest):
    """
    Perform semantic vector search using local HNSW index.
    
    This endpoint:
    1. Generates embedding for the query text
    2. Searches the HNSW vector store for similar chunks
    3. Returns top-k results with metadata
    """
    logger.info(f"Vector search query: {request.query[:50]}...")

    try:
        # Initialize services
        openai_service = OpenAIService()
        vector_store = VectorStore(dimension=1536)

        # Generate query embedding
        query_embedding = await openai_service.generate_embedding(request.query)

        # Search vector store
        results = await vector_store.search(
            query_vector=query_embedding,
            top_k=request.top_k,
            filters=request.filters,
        )

        # Format results
        search_results = [
            SearchResult(
                id=r.get("id", ""),
                content=r.get("content", ""),
                filename=r.get("filename", ""),
                page_number=r.get("page_number"),
                section_title=r.get("section_title"),
                chunk_index=r.get("chunk_index"),
                score=r.get("score", 0.0),
                distance=r.get("distance", 1.0),
            )
            for r in results
        ]

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
        )

    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/stats")
async def get_vector_store_stats():
    """
    Get statistics about the vector store.
    """
    try:
        vector_store = VectorStore(dimension=1536)
        stats = await vector_store.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting vector store stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.post("/clear-index", status_code=status.HTTP_200_OK)
async def clear_vector_index():
    """
    Clear all vectors from the index.
    
    WARNING: This will delete all indexed documents!
    """
    try:
        vector_store = VectorStore(dimension=1536)
        await vector_store.clear()
        return {"message": "Vector index cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing vector index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear index: {str(e)}",
        )

