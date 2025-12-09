"""
Factory for creating appropriate document parsers.
"""
from pathlib import Path
from typing import Optional

from app.parsers.base_parser import BaseParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser
from app.core.logging import get_logger

logger = get_logger(__name__)


class ParserFactory:
    """Factory for creating document parsers based on file type."""

    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 200,
        extract_images: bool = True,
    ):
        """
        Initialize parser factory.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            extract_images: Whether to extract images
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.extract_images = extract_images

        # Register available parsers
        self._parsers = {
            '.pdf': PDFParser,
            '.docx': DOCXParser,
            '.doc': DOCXParser,
        }

    def get_parser(self, filename: str) -> Optional[BaseParser]:
        """
        Get appropriate parser for the given file.

        Args:
            filename: Name of the file to parse

        Returns:
            Parser instance or None if file type not supported
        """
        file_extension = Path(filename).suffix.lower()

        parser_class = self._parsers.get(file_extension)
        if not parser_class:
            logger.warning(f"No parser available for file type: {file_extension}")
            return None

        # Instantiate parser with configuration
        parser = parser_class(
            max_chunk_size=self.max_chunk_size,
            chunk_overlap=self.chunk_overlap,
            extract_images=self.extract_images,
        )

        logger.info(f"Created parser for {file_extension}: {parser_class.__name__}")
        return parser

    def supports_file(self, filename: str) -> bool:
        """
        Check if the file type is supported.

        Args:
            filename: Name of the file

        Returns:
            True if supported, False otherwise
        """
        file_extension = Path(filename).suffix.lower()
        return file_extension in self._parsers

    def supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return list(self._parsers.keys())
