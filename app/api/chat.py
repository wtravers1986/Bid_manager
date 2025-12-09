"""
Chat API endpoint for chatbot functionality.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.openai_service import OpenAIService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Initialize OpenAI service
openai_service = OpenAIService()


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    role: str = "assistant"


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat messages and return AI responses.
    
    Args:
        request: Chat request with message history
        
    Returns:
        Chat response with AI-generated message
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages list cannot be empty")
        
        # Get the last user message
        last_message = request.messages[-1]
        if last_message.role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")
        
        # Convert messages to format expected by OpenAI service
        messages_list = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Generate response using OpenAI service
        response_text = await openai_service.generate_completion(
            messages=messages_list,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        logger.info(f"Generated chat response: {len(response_text)} characters")
        
        return ChatResponse(message=response_text, role="assistant")
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

