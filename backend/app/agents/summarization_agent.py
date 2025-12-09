"""
Agent for generating summaries and consolidated content from multiple sources.
"""
from typing import List, Dict, Any, Optional
import json

from app.agents.base_agent import BaseAgent, AgentResult
from app.services.openai_service import OpenAIService
from app.core.logging import get_logger

logger = get_logger(__name__)


class SummarizationAgent(BaseAgent):
    """
    Agent that creates summaries and consolidated text from candidate passages.

    This agent synthesizes information from multiple source documents,
    creating coherent text with proper citations.
    """

    def __init__(self, openai_service: OpenAIService):
        """
        Initialize summarization agent.

        Args:
            openai_service: OpenAI service instance
        """
        super().__init__(openai_service)

    async def execute(
        self,
        candidates: List[Dict[str, Any]],
        section_title: str,
        section_context: Optional[str] = None,
        target_length: str = "medium",  # short, medium, long
    ) -> AgentResult:
        """
        Generate a consolidated summary from candidate passages.

        Args:
            candidates: List of candidate dicts with content and metadata
            section_title: Title of the section being summarized
            section_context: Optional context about the section
            target_length: Desired length (short: 200w, medium: 500w, long: 1000w)

        Returns:
            AgentResult with generated summary and citations
        """
        try:
            self.logger.info(
                f"Generating {target_length} summary for '{section_title}' "
                f"from {len(candidates)} candidates"
            )

            # Prepare candidate texts with citations
            candidate_texts = []
            for idx, candidate in enumerate(candidates):
                source_info = (
                    f"Source [{idx + 1}]: {candidate.get('source', 'Unknown')} "
                    f"(Page {candidate.get('page_number', 'N/A')})"
                )
                candidate_texts.append(f"{source_info}\n{candidate['content']}\n")

            # Determine target word count
            word_counts = {
                "short": 200,
                "medium": 500,
                "long": 1000,
            }
            target_words = word_counts.get(target_length, 500)

            # Build prompt
            system_message = """You are an expert technical writer specializing in safety procedures
for lifting and rigging operations. Your task is to synthesize information from multiple
source documents into clear, accurate, and well-organized text.

CRITICAL REQUIREMENTS:
1. Maintain safety-critical information exactly as stated
2. Resolve contradictions by noting differences (do not ignore conflicts)
3. Use clear, professional language
4. Include citations using [Source N] notation
5. Organize logically with appropriate structure"""

            context_str = f"\nSection Context: {section_context}" if section_context else ""

            prompt = f"""Create a comprehensive summary for the section: "{section_title}"{context_str}

Target length: approximately {target_words} words

Source passages:
{chr(10).join(candidate_texts)}

Requirements:
1. Synthesize the key information from all relevant sources
2. Cite sources using [Source N] notation where appropriate
3. If sources contradict each other, explicitly note the differences
4. Maintain safety-critical details precisely
5. Structure the content logically

Provide your response as a JSON object with:
{{
  "summary": "The consolidated text with [Source N] citations",
  "key_points": ["point 1", "point 2", ...],
  "citations_used": [1, 2, 3, ...],
  "contradictions_noted": ["description of any contradictions"],
  "confidence": 0.0-1.0
}}

JSON response:"""

            # Generate summary
            response = await self.openai_service.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            # Parse response
            result = json.loads(response)

            # Map citations to candidate IDs
            citations_map = {}
            for source_num in result.get("citations_used", []):
                if 0 < source_num <= len(candidates):
                    candidate = candidates[source_num - 1]
                    citations_map[source_num] = {
                        "chunk_id": candidate.get("chunk_id"),
                        "source": candidate.get("source"),
                        "page_number": candidate.get("page_number"),
                    }

            self.logger.info(f"Generated summary with {len(citations_map)} citations")

            return self._create_success_result(
                {
                    "summary": result.get("summary", ""),
                    "key_points": result.get("key_points", []),
                    "citations_map": citations_map,
                    "contradictions_noted": result.get("contradictions_noted", []),
                    "word_count": len(result.get("summary", "").split()),
                },
                confidence=result.get("confidence", 0.8),
            )

        except Exception as e:
            self.logger.error(f"Error in summarization: {e}")
            return self._create_error_result(str(e))

    async def generate_bullet_summary(
        self,
        candidates: List[Dict[str, Any]],
        num_points: int = 5,
    ) -> AgentResult:
        """
        Generate a bullet-point summary.

        Args:
            candidates: List of candidate passages
            num_points: Number of bullet points to generate

        Returns:
            AgentResult with bullet points
        """
        try:
            # Combine all candidate texts
            combined_text = "\n\n".join(
                c["content"] for c in candidates
            )

            # Extract key points
            key_points = await self.openai_service.extract_key_points(
                combined_text,
                num_points=num_points,
            )

            return self._create_success_result({
                "bullet_points": key_points,
                "count": len(key_points),
            })

        except Exception as e:
            self.logger.error(f"Error generating bullet summary: {e}")
            return self._create_error_result(str(e))

    async def suggest_figures(
        self,
        summary: str,
        available_figures: List[Dict[str, Any]],
        max_suggestions: int = 3,
    ) -> AgentResult:
        """
        Suggest relevant figures for a summary.

        Args:
            summary: The generated summary text
            available_figures: List of figure dicts with captions/descriptions
            max_suggestions: Maximum number of figures to suggest

        Returns:
            AgentResult with figure suggestions
        """
        try:
            self.logger.info(
                f"Suggesting figures from {len(available_figures)} available figures"
            )

            if not available_figures:
                return self._create_success_result({"suggestions": []})

            # Prepare figure descriptions
            figure_descriptions = []
            for idx, fig in enumerate(available_figures):
                desc = f"Figure {idx + 1}: {fig.get('caption', 'No caption')}"
                if fig.get('ocr_text'):
                    desc += f"\nText in figure: {fig['ocr_text'][:200]}"
                figure_descriptions.append(desc)

            # Ask GPT to suggest relevant figures
            system_message = "You are an expert at matching illustrations to technical text."

            prompt = f"""Given this summary text, which figures would be most relevant?

Summary:
{summary}

Available figures:
{chr(10).join(figure_descriptions)}

Return a JSON object with:
{{
  "suggestions": [
    {{
      "figure_index": 0,
      "relevance_score": 0.0-1.0,
      "placement": "before" | "after" | "inline",
      "reason": "why this figure is relevant"
    }}
  ]
}}

Suggest up to {max_suggestions} most relevant figures.

JSON response:"""

            response = await self.openai_service.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            result = json.loads(response)
            suggestions = result.get("suggestions", [])

            # Map back to figure IDs
            for suggestion in suggestions:
                fig_idx = suggestion.get("figure_index")
                if 0 <= fig_idx < len(available_figures):
                    suggestion["figure_id"] = available_figures[fig_idx].get("figure_id")

            self.logger.info(f"Generated {len(suggestions)} figure suggestions")

            return self._create_success_result({
                "suggestions": suggestions,
                "count": len(suggestions),
            })

        except Exception as e:
            self.logger.error(f"Error suggesting figures: {e}")
            return self._create_error_result(str(e))
