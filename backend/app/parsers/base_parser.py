"""
Base parser interface and utilities.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from io import BytesIO
import json


@dataclass
class ParsedChunk:
    """A chunk of text extracted from a document."""
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    token_count: Optional[int] = None
    metadata: Optional[dict] = None

    @property
    def char_count(self) -> int:
        """Get character count."""
        return len(self.content)


@dataclass
class ParsedFigure:
    """A figure extracted from a document."""
    figure_index: int
    page_number: Optional[int] = None
    caption: Optional[str] = None
    figure_number: Optional[str] = None
    image_bytes: Optional[bytes] = None
    image_format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    ocr_text: Optional[str] = None


@dataclass
class ParsedDocument:
    """Complete parsed document with chunks and figures."""
    filename: str
    file_type: str
    chunks: List[ParsedChunk]
    figures: List[ParsedFigure]
    metadata: dict
    full_text: Optional[str] = None
    page_count: Optional[int] = None


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    def __init__(self, max_chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize parser.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    async def parse(
        self,
        file_content: bytes,
        filename: str,
    ) -> ParsedDocument:
        """
        Parse a document from bytes.

        Args:
            file_content: Raw bytes of the document
            filename: Original filename

        Returns:
            ParsedDocument with chunks and figures
        """
        pass

    @abstractmethod
    def supports_file_type(self, file_extension: str) -> bool:
        """Check if this parser supports the given file type."""
        pass

    def chunk_text(
        self,
        text: str,
        section_title: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> List[ParsedChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            section_title: Optional section title for chunks
            page_number: Optional page number

        Returns:
            List of ParsedChunk objects
        """
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.max_chunk_size

            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + 1
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    ParsedChunk(
                        content=chunk_text,
                        chunk_index=chunk_index,
                        page_number=page_number,
                        section_title=section_title,
                    )
                )
                chunk_index += 1

            # Move start position, accounting for overlap
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def extract_metadata(self, raw_metadata: dict) -> dict:
        """
        Extract and normalize metadata from document.

        Args:
            raw_metadata: Raw metadata from document

        Returns:
            Normalized metadata dictionary
        """
        metadata = {}

        # Common metadata fields
        fields_map = {
            'title': ['title', 'Title', 'dc:title'],
            'author': ['author', 'Author', 'creator', 'dc:creator'],
            'subject': ['subject', 'Subject', 'dc:subject'],
            'created': ['created', 'CreationDate', 'creation_date', 'dcterms:created'],
            'modified': ['modified', 'ModDate', 'modification_date', 'dcterms:modified'],
            'version': ['version', 'Version', 'revision'],
        }

        for key, possible_keys in fields_map.items():
            for possible_key in possible_keys:
                if possible_key in raw_metadata:
                    metadata[key] = raw_metadata[possible_key]
                    break

        return metadata
    
    async def chunk_text_with_llm(
        self,
        text: str,
        openai_service,
        section_title: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> List[ParsedChunk]:
        """
        Split text into logical chunks using LLM analysis.
        Uses rolling window approach: 5k tokens with 1k token overlap.
        
        Args:
            text: Text to chunk
            openai_service: OpenAIService instance for LLM calls
            section_title: Optional section title for chunks
            page_number: Optional page number
            
        Returns:
            List of ParsedChunk objects with logical boundaries
        """
        if not text or not text.strip():
            return []
        
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        # Token limits
        WINDOW_SIZE_TOKENS = 5000
        OVERLAP_TOKENS = 1000
        STEP_SIZE_TOKENS = WINDOW_SIZE_TOKENS - OVERLAP_TOKENS  # 4000 tokens
        
        all_chunks = []
        chunk_index = 0
        
        # Convert text to approximate tokens (rough estimate: 1 token ≈ 4 chars)
        # More accurate: use tokenizer
        text_tokens = openai_service.count_tokens(text)
        
        logger.info(f"Chunking text with LLM: {text_tokens} tokens, {len(text)} characters")
        
        # Process text in rolling windows
        current_pos = 0
        processed_text = ""
        
        while current_pos < len(text):
            # Get window of text (approximate token position)
            # Estimate: 4 chars per token
            window_start_chars = int(current_pos)
            window_end_chars = min(len(text), window_start_chars + (WINDOW_SIZE_TOKENS * 4))
            
            window_text = text[window_start_chars:window_end_chars]
            
            # Count actual tokens in window
            window_tokens = openai_service.count_tokens(window_text)
            
            # Adjust if needed to stay within token limit
            if window_tokens > WINDOW_SIZE_TOKENS:
                # Need to trim - find a good break point
                target_chars = int((WINDOW_SIZE_TOKENS / window_tokens) * len(window_text))
                # Try to break at sentence boundary
                for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                    last_punct = window_text.rfind(punct, 0, target_chars)
                    if last_punct != -1:
                        window_text = window_text[:last_punct + 1]
                        break
                else:
                    window_text = window_text[:target_chars]
            
            # Add context from previous window if not first window
            if current_pos > 0 and processed_text:
                # Get last part of processed text for context
                context_text = processed_text[-OVERLAP_TOKENS * 4:] if len(processed_text) > OVERLAP_TOKENS * 4 else processed_text
                full_window_text = context_text + "\n\n---CONTINUATION---\n\n" + window_text
            else:
                full_window_text = window_text
            
            try:
                # Ask LLM to create logical chunks
                prompt = f"""You are an expert document analyst. Your task is to split the following text into logical, well-defined chunks at the paragraph level.

TEXT TO CHUNK:
{full_window_text}

INSTRUCTIONS:
1. Analyze the text and identify logical paragraph boundaries
2. Create chunks that:
   - Are complete, coherent paragraphs or groups of related paragraphs
   - Make sense as standalone units
   - Are at natural break points (end of paragraph, section, etc.)
   - Do NOT cut off mid-sentence or mid-thought
3. If text at the BEGINNING of the window doesn't form a complete logical unit, you may IGNORE it
4. If text at the END of the window doesn't form a complete logical unit, you may IGNORE it
5. Focus on creating clean, meaningful chunks

OUTPUT FORMAT:
Return a JSON object with a "chunks" array. Each chunk object must have:
- "content": The chunk text (string)
- "start_index": Character position where chunk starts in the provided text (integer, 0-based)
- "end_index": Character position where chunk ends (integer, exclusive)

IMPORTANT:
- Only include chunks that are complete and logical
- You may skip incomplete text at the beginning or end
- Return ONLY valid JSON, no explanatory text

Example format:
{{
  "chunks": [
    {{
      "content": "First complete paragraph...",
      "start_index": 0,
      "end_index": 150
    }},
    {{
      "content": "Second complete paragraph...",
      "start_index": 150,
      "end_index": 300
    }}
  ]
}}"""

                system_message = """You are an expert at analyzing document structure and identifying logical text boundaries.
Your task is to split text into meaningful, complete chunks at the paragraph level."""

                response = await openai_service.generate_completion(
                    prompt=prompt,
                    system_message=system_message,
                    temperature=0.2,  # Low temperature for consistent chunking
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                
                # Parse LLM response
                result = json.loads(response)
                llm_chunks = result.get('chunks', [])
                
                if not isinstance(llm_chunks, list):
                    logger.warning("LLM did not return chunks array, using fallback")
                    llm_chunks = []
                
                # Process LLM chunks
                for llm_chunk in llm_chunks:
                    if not isinstance(llm_chunk, dict):
                        continue
                    
                    chunk_content = llm_chunk.get('content', '').strip()
                    if not chunk_content:
                        continue
                    
                    # Adjust indices to absolute position in original text
                    relative_start = llm_chunk.get('start_index', 0)
                    relative_end = llm_chunk.get('end_index', len(chunk_content))
                    
                    # If we have context, adjust for it
                    if current_pos > 0 and processed_text:
                        # Find the chunk in the full window text
                        context_len = len(context_text) + len("\n\n---CONTINUATION---\n\n")
                        # The chunk should be in the new part, not the context
                        if relative_start >= context_len:
                            # Valid chunk in new text
                            actual_start = window_start_chars + (relative_start - context_len)
                            actual_end = window_start_chars + (relative_end - context_len)
                        else:
                            # Chunk overlaps with context - skip to avoid duplicates
                            continue
                    else:
                        actual_start = window_start_chars + relative_start
                        actual_end = window_start_chars + relative_end
                    
                    # Create ParsedChunk
                    token_count = openai_service.count_tokens(chunk_content)
                    
                    all_chunks.append(
                        ParsedChunk(
                            content=chunk_content,
                            chunk_index=chunk_index,
                            page_number=page_number,
                            section_title=section_title,
                            token_count=token_count,
                        )
                    )
                    chunk_index += 1
                
                # Track processed text (for overlap detection)
                # Use the actual window text that was processed
                processed_text = window_text
                
                # Move to next window (with overlap)
                # Move forward by step size
                current_pos += STEP_SIZE_TOKENS * 4  # Approximate char position
                
                # If we're near the end, process remaining text
                if current_pos >= len(text) - (STEP_SIZE_TOKENS * 2):
                    # Process remaining text as final window
                    remaining_text = text[int(current_pos - OVERLAP_TOKENS * 4):]
                    if remaining_text.strip() and len(remaining_text) > 100:
                        # Recursively process remaining (but limit depth)
                        remaining_chunks = await self._chunk_remaining_text(
                            remaining_text,
                            openai_service,
                            section_title,
                            page_number,
                            chunk_index
                        )
                        all_chunks.extend(remaining_chunks)
                    break
                
            except Exception as e:
                logger.error(f"Error in LLM chunking at position {current_pos}: {e}")
                # Fallback to regular chunking for this window
                fallback_chunks = self.chunk_text(
                    window_text,
                    section_title=section_title,
                    page_number=page_number
                )
                # Update indices
                for chunk in fallback_chunks:
                    chunk.chunk_index = chunk_index
                    chunk_index += 1
                all_chunks.extend(fallback_chunks)
                
                # Move forward
                current_pos += STEP_SIZE_TOKENS * 4
        
        # Remove duplicates (chunks with same content)
        seen_contents = set()
        unique_chunks = []
        for chunk in all_chunks:
            content_hash = hash(chunk.content[:100])  # Hash first 100 chars
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_chunks.append(chunk)
            else:
                # Update index for skipped chunk
                chunk_index -= 1
        
        # Re-index chunks
        for idx, chunk in enumerate(unique_chunks):
            chunk.chunk_index = idx
        
        logger.info(f"LLM chunking created {len(unique_chunks)} logical chunks from {text_tokens} tokens")
        
        return unique_chunks
    
    async def _chunk_remaining_text(
        self,
        text: str,
        openai_service,
        section_title: Optional[str],
        page_number: Optional[int],
        start_chunk_index: int
    ) -> List[ParsedChunk]:
        """Helper to chunk remaining text at the end."""
        chunks = []
        chunk_index = start_chunk_index
        
        # Simple approach: use LLM for final chunk
        try:
            prompt = f"""Split the following text into logical paragraph-level chunks.

TEXT:
{text}

Return JSON with "chunks" array. Each chunk: {{"content": "...", "start_index": 0, "end_index": N}}
Only include complete, logical chunks. You may ignore incomplete text at the end.

Return ONLY valid JSON."""

            response = await openai_service.generate_completion(
                prompt=prompt,
                system_message="Split text into logical paragraph chunks.",
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            llm_chunks = result.get('chunks', [])
            
            for llm_chunk in llm_chunks:
                if isinstance(llm_chunk, dict):
                    content = llm_chunk.get('content', '').strip()
                    if content:
                        chunks.append(
                            ParsedChunk(
                                content=content,
                                chunk_index=chunk_index,
                                page_number=page_number,
                                section_title=section_title,
                                token_count=openai_service.count_tokens(content),
                            )
                        )
                        chunk_index += 1
        except Exception:
            # Fallback to regular chunking
            fallback = self.chunk_text(text, section_title, page_number)
            for chunk in fallback:
                chunk.chunk_index = chunk_index
                chunk_index += 1
            chunks.extend(fallback)
        
        return chunks
