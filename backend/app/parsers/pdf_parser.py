"""
PDF document parser using PyMuPDF (fitz).
"""
import io
from typing import Optional
import fitz  # PyMuPDF
from PIL import Image

from app.parsers.base_parser import (
    BaseParser,
    ParsedDocument,
    ParsedChunk,
    ParsedFigure,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF documents."""

    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 200,
        extract_images: bool = True,
        min_image_size: int = 100,  # Minimum width/height in pixels
    ):
        """
        Initialize PDF parser.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            extract_images: Whether to extract images
            min_image_size: Minimum image dimensions to extract
        """
        super().__init__(max_chunk_size, chunk_overlap)
        self.extract_images = extract_images
        self.min_image_size = min_image_size

    def supports_file_type(self, file_extension: str) -> bool:
        """Check if this parser supports the file type."""
        return file_extension.lower() in ['.pdf']

    async def parse(
        self,
        file_content: bytes,
        filename: str,
    ) -> ParsedDocument:
        """
        Parse a PDF document.

        Args:
            file_content: Raw PDF bytes
            filename: Original filename

        Returns:
            ParsedDocument with extracted content
        """
        logger.info(f"Parsing PDF document: {filename}")

        # Open PDF from bytes
        pdf_document = fitz.open(stream=file_content, filetype="pdf")

        try:
            # Extract metadata
            metadata = self.extract_metadata(pdf_document.metadata)
            metadata['page_count'] = len(pdf_document)

            # Extract text and create chunks
            chunks = []
            full_text_parts = []

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_text = page.get_text()

                if page_text.strip():
                    full_text_parts.append(page_text)

            full_text = '\n\n'.join(full_text_parts)
            
            # Use LLM chunking if available, otherwise use regular chunking
            # Note: openai_service should be passed via a class attribute or parameter
            # For now, we'll use regular chunking and add LLM chunking option later
            # This will be handled at the service level
            if hasattr(self, 'openai_service') and self.openai_service:
                # Use LLM-based chunking for better paragraph boundaries
                chunks = await self.chunk_text_with_llm(
                    full_text,
                    self.openai_service,
                    page_number=1,  # Will be set per chunk if needed
                )
            else:
                # Fallback to regular chunking
                chunk_index = 0
                for page_num, page_text in enumerate(full_text_parts, 1):
                    page_chunks = self.chunk_text(
                        page_text,
                        page_number=page_num,
                    )
                    for chunk in page_chunks:
                        chunk.chunk_index = chunk_index
                        chunk_index += 1
                        chunks.append(chunk)

            # Extract figures/images
            figures = []
            if self.extract_images:
                figures = await self._extract_images(pdf_document)

            logger.info(
                f"Parsed PDF: {len(chunks)} chunks, {len(figures)} figures, "
                f"{len(pdf_document)} pages"
            )

            return ParsedDocument(
                filename=filename,
                file_type='pdf',
                chunks=chunks,
                figures=figures,
                metadata=metadata,
                full_text=full_text,
                page_count=len(pdf_document),
            )

        finally:
            pdf_document.close()

    async def _extract_images(self, pdf_document: fitz.Document) -> list[ParsedFigure]:
        """
        Extract images from PDF document.

        Args:
            pdf_document: Opened PDF document

        Returns:
            List of ParsedFigure objects
        """
        figures = []
        figure_index = 0

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Get image dimensions
                    img_obj = Image.open(io.BytesIO(image_bytes))
                    width, height = img_obj.size

                    # Skip small images (likely logos or icons)
                    if width < self.min_image_size or height < self.min_image_size:
                        continue

                    # Try to find caption nearby (simplified heuristic)
                    caption = self._find_caption_for_image(page, img_index)

                    figures.append(
                        ParsedFigure(
                            figure_index=figure_index,
                            page_number=page_num + 1,
                            caption=caption,
                            image_bytes=image_bytes,
                            image_format=image_ext,
                            width=width,
                            height=height,
                        )
                    )
                    figure_index += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index} from page {page_num + 1}: {e}"
                    )
                    continue

        return figures

    def _find_caption_for_image(
        self,
        page: fitz.Page,
        img_index: int,
    ) -> Optional[str]:
        """
        Try to find caption text for an image.

        This is a heuristic approach looking for text near the image
        that starts with "Figure", "Fig.", "Diagram", etc.

        Args:
            page: PDF page object
            img_index: Index of image on page

        Returns:
            Caption text if found, None otherwise
        """
        text = page.get_text()
        lines = text.split('\n')

        # Look for lines starting with figure indicators
        figure_indicators = ['Figure', 'Fig.', 'Diagram', 'Image', 'Photo']

        for line in lines:
            line_stripped = line.strip()
            for indicator in figure_indicators:
                if line_stripped.startswith(indicator):
                    # Take this line and possibly the next one
                    return line_stripped[:200]  # Limit caption length

        return None
