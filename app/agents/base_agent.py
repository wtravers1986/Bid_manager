"""
Base agent interface for AI-powered analysis tasks.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass

from app.services.openai_service import OpenAIService
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResult:
    """Result from an agent execution."""
    success: bool
    data: Dict[str, Any]
    error: str | None = None
    confidence: float | None = None


class BaseAgent(ABC):
    """Base class for AI agents."""

    def __init__(self, openai_service: OpenAIService):
        """
        Initialize agent.

        Args:
            openai_service: OpenAI service instance
        """
        self.openai_service = openai_service
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        """
        Execute the agent's task.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            AgentResult with task output
        """
        pass

    def _create_success_result(
        self,
        data: Dict[str, Any],
        confidence: float | None = None,
    ) -> AgentResult:
        """Create a successful result."""
        return AgentResult(
            success=True,
            data=data,
            confidence=confidence,
        )

    def _create_error_result(self, error: str) -> AgentResult:
        """Create an error result."""
        return AgentResult(
            success=False,
            data={},
            error=error,
        )
