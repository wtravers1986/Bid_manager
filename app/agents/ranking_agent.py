"""
Agent for ranking and prioritizing candidate passages.
"""
from typing import List, Dict, Any
import json

from app.agents.base_agent import BaseAgent, AgentResult
from app.services.openai_service import OpenAIService
from app.core.logging import get_logger

logger = get_logger(__name__)


class RankingAgent(BaseAgent):
    """
    Agent that ranks candidate passages by relevance and quality.

    This helps prioritize which source passages should be used
    in the consolidated output.
    """

    def __init__(self, openai_service: OpenAIService):
        """
        Initialize ranking agent.

        Args:
            openai_service: OpenAI service instance
        """
        super().__init__(openai_service)

    async def execute(
        self,
        candidates: List[Dict[str, Any]],
        section_title: str,
        section_requirements: str | None = None,
        criteria: List[str] | None = None,
    ) -> AgentResult:
        """
        Rank candidates by relevance and quality.

        Args:
            candidates: List of candidate dicts
            section_title: Title of the section
            section_requirements: Optional requirements for the section
            criteria: Optional list of ranking criteria

        Returns:
            AgentResult with ranked candidates
        """
        try:
            self.logger.info(
                f"Ranking {len(candidates)} candidates for '{section_title}'"
            )

            if not candidates:
                return self._create_success_result({"ranked_candidates": []})

            # Default ranking criteria
            if criteria is None:
                criteria = [
                    "Relevance to section topic",
                    "Completeness of information",
                    "Clarity and readability",
                    "Technical accuracy",
                    "Safety information coverage",
                    "Recency of information",
                ]

            # Prepare candidate summaries for ranking
            candidate_summaries = []
            for idx, candidate in enumerate(candidates):
                summary = {
                    "index": idx,
                    "preview": candidate["content"][:300] + "...",
                    "source": candidate.get("source", "Unknown"),
                    "page": candidate.get("page_number", "N/A"),
                    "date": candidate.get("document_date", "Unknown"),
                }
                candidate_summaries.append(summary)

            # Build ranking prompt
            system_message = """You are an expert at evaluating technical documentation for
lifting and rigging operations. Rank passages based on their relevance, quality,
and suitability for inclusion in a consolidated procedure."""

            requirements_str = (
                f"\n\nSection Requirements:\n{section_requirements}"
                if section_requirements
                else ""
            )

            prompt = f"""Rank these candidate passages for the section: "{section_title}"{requirements_str}

Ranking Criteria:
{chr(10).join(f"- {c}" for c in criteria)}

Candidates:
{json.dumps(candidate_summaries, indent=2)}

Return a JSON object with:
{{
  "rankings": [
    {{
      "index": 0,
      "rank": 1,
      "score": 0.0-1.0,
      "relevance_score": 0.0-1.0,
      "quality_score": 0.0-1.0,
      "reasoning": "Brief explanation of ranking",
      "strengths": ["strength 1", "strength 2"],
      "weaknesses": ["weakness 1", "weakness 2"],
      "recommendation": "include" | "consider" | "exclude"
    }}
  ],
  "overall_assessment": "Brief assessment of available candidates"
}}

JSON response:"""

            response = await self.openai_service.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            result = json.loads(response)
            rankings = result.get("rankings", [])

            # Sort by rank
            rankings.sort(key=lambda x: x.get("rank", 999))

            # Add candidate IDs to rankings
            for ranking in rankings:
                idx = ranking.get("index")
                if 0 <= idx < len(candidates):
                    ranking["chunk_id"] = candidates[idx].get("chunk_id")
                    ranking["source_document_id"] = candidates[idx].get(
                        "source_document_id"
                    )

            self.logger.info(f"Ranked {len(rankings)} candidates")

            # Count recommendations
            include_count = sum(
                1 for r in rankings if r.get("recommendation") == "include"
            )
            consider_count = sum(
                1 for r in rankings if r.get("recommendation") == "consider"
            )

            return self._create_success_result({
                "rankings": rankings,
                "overall_assessment": result.get("overall_assessment", ""),
                "include_count": include_count,
                "consider_count": consider_count,
                "exclude_count": len(rankings) - include_count - consider_count,
            })

        except Exception as e:
            self.logger.error(f"Error in ranking: {e}")
            return self._create_error_result(str(e))

    async def assess_coverage(
        self,
        candidates: List[Dict[str, Any]],
        required_topics: List[str],
    ) -> AgentResult:
        """
        Assess how well candidates cover required topics.

        Args:
            candidates: List of candidate passages
            required_topics: List of topics that must be covered

        Returns:
            AgentResult with coverage assessment
        """
        try:
            self.logger.info(
                f"Assessing coverage of {len(required_topics)} topics "
                f"across {len(candidates)} candidates"
            )

            # Combine candidate texts
            combined_text = "\n\n".join(
                f"Candidate {i}: {c['content']}"
                for i, c in enumerate(candidates)
            )

            system_message = """You are an expert at analyzing technical documentation
for completeness and coverage."""

            prompt = f"""Assess how well these candidates cover the required topics.

Required Topics:
{chr(10).join(f"- {t}" for t in required_topics)}

Candidate Passages:
{combined_text[:4000]}

Return a JSON object with:
{{
  "coverage": [
    {{
      "topic": "topic name",
      "is_covered": true/false,
      "coverage_quality": "excellent" | "good" | "partial" | "missing",
      "covered_by_candidates": [0, 1, 2],
      "gaps": "Description of any gaps"
    }}
  ],
  "overall_coverage_score": 0.0-1.0,
  "recommendations": ["recommendation 1", "recommendation 2"]
}}

JSON response:"""

            response = await self.openai_service.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            result = json.loads(response)

            coverage = result.get("coverage", [])
            covered_count = sum(1 for c in coverage if c.get("is_covered", False))

            self.logger.info(
                f"Coverage: {covered_count}/{len(required_topics)} topics covered"
            )

            return self._create_success_result({
                "coverage": coverage,
                "overall_score": result.get("overall_coverage_score", 0.0),
                "recommendations": result.get("recommendations", []),
                "covered_topics": covered_count,
                "missing_topics": len(required_topics) - covered_count,
            })

        except Exception as e:
            self.logger.error(f"Error in coverage assessment: {e}")
            return self._create_error_result(str(e))
