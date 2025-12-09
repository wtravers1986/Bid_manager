"""Document parsers."""
from app.parsers.base_parser import (
    BaseParser,
    ParsedDocument,
    ParsedChunk,
    ParsedFigure,
)
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser
from app.parsers.parser_factory import ParserFactory

__all__ = [
    "BaseParser",
    "ParsedDocument",
    "ParsedChunk",
    "ParsedFigure",
    "PDFParser",
    "DOCXParser",
    "ParserFactory",
]
