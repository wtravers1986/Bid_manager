"""
Agent for detecting contradictions and overlaps between text passages.
"""
from typing import List, Dict, Any
from itertools import combinations

from app.agents.base_agent import BaseAgent, AgentResult
from app.services.openai_service import OpenAIService
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContradictionAgent(BaseAgent):
    """
    Agent that detects contradictions and overlaps between candidate passages.

    This is critical for the document cleanup process as it identifies
    conflicting information that needs human review.
    """

    def __init__(
        self,
        openai_service: OpenAIService,
        confidence_threshold: float = 0.6,
    ):
        """
        Initialize contradiction detection agent.

        Args:
            openai_service: OpenAI service instance
            confidence_threshold: Minimum confidence to report a contradiction
        """
        super().__init__(openai_service)
        self.confidence_threshold = confidence_threshold

    async def execute(
        self,
        candidates: List[Dict[str, Any]],
        section_context: str | None = None,
    ) -> AgentResult:
        """
        Detect contradictions between candidate passages.

        Args:
            candidates: List of candidate dicts with 'content', 'source', 'chunk_id'
            section_context: Optional context about the section being analyzed

        Returns:
            AgentResult with list of detected conflicts
        """
        try:
            self.logger.info(f"Analyzing {len(candidates)} candidates for contradictions")

            if len(candidates) < 2:
                return self._create_success_result({
                    "conflicts": [],
                    "total_comparisons": 0,
                })

            conflicts = []
            total_comparisons = 0

            # Compare all pairs of candidates
            for (idx_a, candidate_a), (idx_b, candidate_b) in combinations(
                enumerate(candidates), 2
            ):
                total_comparisons += 1

                # Perform contradiction detection
                result = await self.openai_service.detect_contradictions(
                    text_a=candidate_a["content"],
                    text_b=candidate_b["content"],
                    source_a=candidate_a.get("source", f"Candidate {idx_a}"),
                    source_b=candidate_b.get("source", f"Candidate {idx_b}"),
                )

                # Check if contradiction meets threshold
                if (
                    result.get("has_contradiction", False)
                    and result.get("confidence", 0.0) >= self.confidence_threshold
                ):
                    conflicts.append({
                        "candidate_a_id": candidate_a.get("chunk_id"),
                        "candidate_b_id": candidate_b.get("chunk_id"),
                        "candidate_a_idx": idx_a,
                        "candidate_b_idx": idx_b,
                        "conflict_type": result.get("contradiction_type"),
                        "description": result.get("description"),
                        "confidence": result.get("confidence"),
                        "severity": result.get("severity"),
                        "affected_topics": result.get("affected_topics", []),
                    })

            self.logger.info(
                f"Found {len(conflicts)} contradictions from {total_comparisons} comparisons"
            )

            return self._create_success_result({
                "conflicts": conflicts,
                "total_comparisons": total_comparisons,
                "high_severity_count": sum(
                    1 for c in conflicts if c.get("severity") == "high"
                ),
            })

        except Exception as e:
            self.logger.error(f"Error in contradiction detection: {e}")
            return self._create_error_result(str(e))

    async def detect_overlap(
        self,
        candidates: List[Dict[str, Any]],
        similarity_threshold: float = 0.8,
    ) -> AgentResult:
        """
        Detect overlapping content between candidates.

        Args:
            candidates: List of candidate dicts
            similarity_threshold: Threshold for considering content as overlapping

        Returns:
            AgentResult with overlap information
        """
        try:
            self.logger.info(f"Analyzing {len(candidates)} candidates for overlaps")

            if len(candidates) < 2:
                return self._create_success_result({"overlaps": []})

            # Generate embeddings for all candidates
            texts = [c["content"] for c in candidates]
            embeddings = await self.openai_service.generate_embeddings_batch(texts)

            # Calculate cosine similarity between all pairs
            overlaps = []
            for (idx_a, emb_a), (idx_b, emb_b) in combinations(
                enumerate(embeddings), 2
            ):
                similarity = self._cosine_similarity(emb_a, emb_b)

                if similarity >= similarity_threshold:
                    overlaps.append({
                        "candidate_a_id": candidates[idx_a].get("chunk_id"),
                        "candidate_b_id": candidates[idx_b].get("chunk_id"),
                        "candidate_a_idx": idx_a,
                        "candidate_b_idx": idx_b,
                        "similarity_score": similarity,
                        "is_duplicate": similarity > 0.95,
                    })

            self.logger.info(f"Found {len(overlaps)} overlapping passages")

            return self._create_success_result({
                "overlaps": overlaps,
                "duplicate_count": sum(1 for o in overlaps if o["is_duplicate"]),
            })

        except Exception as e:
            self.logger.error(f"Error in overlap detection: {e}")
            return self._create_error_result(str(e))

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
