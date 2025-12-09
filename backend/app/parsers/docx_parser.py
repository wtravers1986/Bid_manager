"""
DOCX document parser using python-docx.
"""
import io
from typing import Optional
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

from app.parsers.base_parser import (
    BaseParser,
    ParsedDocument,
    ParsedChunk,
    ParsedFigure,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class DOCXParser(BaseParser):
    """Parser for DOCX documents."""

    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 200,
        extract_images: bool = True,
    ):
        """
        Initialize DOCX parser.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            extract_images: Whether to extract images
        """
        super().__init__(max_chunk_size, chunk_overlap)
        self.extract_images = extract_images

    def supports_file_type(self, file_extension: str) -> bool:
        """Check if this parser supports the file type."""
        return file_extension.lower() in ['.docx', '.doc']

    async def parse(
        self,
        file_content: bytes,
        filename: str,
    ) -> ParsedDocument:
        """
        Parse a DOCX document.

        Args:
            file_content: Raw DOCX bytes
            filename: Original filename

        Returns:
            ParsedDocument with extracted content
        """
        logger.info(f"Parsing DOCX document: {filename}")

        # Open document from bytes
        doc = Document(io.BytesIO(file_content))

        # Extract metadata
        metadata = {}
        if hasattr(doc, 'core_properties'):
            cp = doc.core_properties
            metadata = {
                'title': cp.title or '',
                'author': cp.author or '',
                'subject': cp.subject or '',
                'created': str(cp.created) if cp.created else None,
                'modified': str(cp.modified) if cp.modified else None,
                'version': cp.revision or '',
            }

        # Extract text with structure
        full_text_parts = []
        current_section = None

        for element in doc.element.body:
            if isinstance(element, CT_P):
                para = Paragraph(element, doc)
                text = para.text.strip()

                if not text:
                    continue

                # Check if this is a heading
                if para.style.name.startswith('Heading'):
                    current_section = text
                    full_text_parts.append(f"\n## {text}\n")
                else:
                    full_text_parts.append(text)

            elif isinstance(element, CT_Tbl):
                # Handle tables
                table = Table(element, doc)
                table_text = self._extract_table_text(table)
                if table_text:
                    full_text_parts.append(table_text)

        full_text = '\n'.join(full_text_parts)
        
        # Use LLM chunking if available, otherwise use regular chunking
        if hasattr(self, 'openai_service') and self.openai_service:
            # Use LLM-based chunking for better paragraph boundaries
            chunks = await self.chunk_text_with_llm(
                full_text,
                self.openai_service,
                section_title=current_section,
            )
        else:
            # Fallback to regular chunking
            chunks = []
            chunk_index = 0
            current_section = None
            for element in doc.element.body:
                if isinstance(element, CT_P):
                    para = Paragraph(element, doc)
                    text = para.text.strip()

                    if not text:
                        continue

                    # Check if this is a heading
                    if para.style.name.startswith('Heading'):
                        current_section = text
                    else:
                        # Create chunks for paragraph
                        para_chunks = self.chunk_text(
                            text,
                            section_title=current_section,
                        )

                        # Update chunk indices
                        for chunk in para_chunks:
                            chunk.chunk_index = chunk_index
                            chunk_index += 1
                            chunks.append(chunk)
                
                elif isinstance(element, CT_Tbl):
                    # Handle tables
                    table = Table(element, doc)
                    table_text = self._extract_table_text(table)
                    if table_text:
                        # Create chunks for table
                        table_chunks = self.chunk_text(
                            table_text,
                            section_title=current_section,
                        )

                        for chunk in table_chunks:
                            chunk.chunk_index = chunk_index
                            chunk_index += 1
                            chunks.append(chunk)

        # Extract images
        figures = []
        if self.extract_images:
            figures = await self._extract_images(doc)

        logger.info(
            f"Parsed DOCX: {len(chunks)} chunks, {len(figures)} figures"
        )

        return ParsedDocument(
            filename=filename,
            file_type='docx',
            chunks=chunks,
            figures=figures,
            metadata=metadata,
            full_text=full_text,
            page_count=None,  # DOCX doesn't have explicit page count
        )

    def _extract_table_text(self, table: Table) -> str:
        """
        Extract text from a table in readable format.

        Args:
            table: Table object

        Returns:
            Formatted table text
        """
        rows_text = []
        for row in table.rows:
            cells_text = [cell.text.strip() for cell in row.cells]
            if any(cells_text):  # Skip empty rows
                rows_text.append(' | '.join(cells_text))

        return '\n'.join(rows_text)

    async def _extract_images(self, doc: Document) -> list[ParsedFigure]:
        """
        Extract images from DOCX document.

        Args:
            doc: Document object

        Returns:
            List of ParsedFigure objects
        """
        figures = []
        figure_index = 0

        # Iterate through all relationships to find images
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    image_part = rel.target_part
                    image_bytes = image_part.blob
                    image_ext = image_part.content_type.split('/')[-1]

                    # Try to get dimensions
                    from PIL import Image
                    img = Image.open(io.BytesIO(image_bytes))
                    width, height = img.size

                    figures.append(
                        ParsedFigure(
                            figure_index=figure_index,
                            image_bytes=image_bytes,
                            image_format=image_ext,
                            width=width,
                            height=height,
                        )
                    )
                    figure_index += 1

                except Exception as e:
                    logger.warning(f"Failed to extract image: {e}")
                    continue

        return figures
