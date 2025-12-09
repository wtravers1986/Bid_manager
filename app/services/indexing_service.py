"""
Service for indexing documents from the data folder into local HNSW vector store.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

from app.services.storage_service import StorageService
from app.services.openai_service import OpenAIService
from app.services.vector_store import VectorStore
from app.parsers import ParserFactory
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class IndexingService:
    """Service for processing and indexing documents."""

    def __init__(self):
        """Initialize indexing service."""
        self.storage_service = StorageService()
        self.openai_service = OpenAIService()
        self.vector_store = VectorStore(dimension=1536)  # ada-002 dimension
        self.parser_factory = ParserFactory()

    async def create_index_if_not_exists(self) -> bool:
        """
        Initialize local HNSW vector store.

        Returns:
            True if index was initialized
        """
        try:
            logger.info("Initializing local HNSW vector store...")
            # Vector store is initialized in __init__, just verify it's ready
            stats = await self.vector_store.get_stats()
            logger.info(f"Vector store ready: {stats['total_vectors']} vectors")
            return True
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise

    async def process_and_index_documents(
        self,
        session_id: Optional[int] = None,
        document_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Process documents from data folder and index them in local HNSW vector store.

        Args:
            session_id: Optional session ID to filter documents
            document_ids: Optional list of specific document IDs to process

        Returns:
            Dictionary with indexing results
        """
        try:
            # Ensure index exists
            await self.create_index_if_not_exists()

            # Get documents from data folder
            data_dir = self.storage_service.data_dir
            all_files = []

            if data_dir.exists():
                for file_path in data_dir.iterdir():
                    if file_path.is_file():
                        ext = file_path.suffix.lower()
                        if ext in [".pdf", ".docx", ".doc"]:
                            all_files.append(file_path)

            if not all_files:
                logger.warning("No documents found in data folder")
                return {
                    "success": False,
                    "message": "No documents found in data folder",
                    "processed": 0,
                    "indexed_chunks": 0,
                }

            logger.info(f"Found {len(all_files)} documents to process")

            total_chunks = 0
            processed_docs = 0
            failed_docs = []

            # Process each document
            for file_path in all_files:
                try:
                    logger.info(f"Processing document: {file_path.name}")

                    # Read file
                    file_content = file_path.read_bytes()

                    # Parse document
                    parser = self.parser_factory.get_parser(file_path.name)
                    # Pass openai_service to parser for LLM chunking
                    parser.openai_service = self.openai_service
                    parsed_doc = await parser.parse(file_content, file_path.name)

                    if not parsed_doc.chunks:
                        logger.warning(f"No chunks extracted from {file_path.name}")
                        continue

                    # Generate embeddings for all chunks
                    chunk_texts = [chunk.content for chunk in parsed_doc.chunks]
                    logger.info(
                        f"Generating embeddings for {len(chunk_texts)} chunks from {file_path.name}"
                    )

                    embeddings = await self.openai_service.generate_embeddings_batch(
                        chunk_texts, batch_size=100  # Larger batch size for better performance
                    )

                    if len(embeddings) != len(parsed_doc.chunks):
                        logger.warning(
                            f"Embedding count mismatch: {len(embeddings)} embeddings "
                            f"for {len(parsed_doc.chunks)} chunks"
                        )
                        # Skip this document if embedding generation failed
                        continue

                    # Prepare chunks for indexing
                    vector_ids = []
                    vectors = []
                    metadata_list = []
                    
                    for idx, (chunk, embedding) in enumerate(
                        zip(parsed_doc.chunks, embeddings)
                    ):
                        # Create unique ID for chunk
                        chunk_hash = hashlib.md5(
                            f"{file_path.name}_{idx}_{chunk.content[:100]}".encode()
                        ).hexdigest()
                        vector_id = f"{chunk_hash}_{idx}"

                        # Prepare metadata
                        metadata = {
                            "content": chunk.content,
                            "filename": file_path.name,
                            "page_number": chunk.page_number,
                            "section_title": chunk.section_title,
                            "chunk_index": chunk.chunk_index,
                            "session_id": session_id if session_id else 0,
                            "file_type": parsed_doc.file_type,
                            "page_count": parsed_doc.page_count or 0,
                        }

                        vector_ids.append(vector_id)
                        vectors.append(embedding)
                        metadata_list.append(metadata)

                    # Add vectors to HNSW index
                    indexed_count = await self.vector_store.add_vectors(
                        vectors=vectors,
                        ids=vector_ids,
                        metadata_list=metadata_list,
                    )

                    total_chunks += indexed_count
                    processed_docs += 1

                    logger.info(
                        f"Indexed {indexed_count} chunks from {file_path.name}"
                    )

                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {e}")
                    failed_docs.append({"filename": file_path.name, "error": str(e)})
                    continue

            result = {
                "success": True,
                "message": f"Processed {processed_docs} documents, indexed {total_chunks} chunks",
                "processed": processed_docs,
                "failed": len(failed_docs),
                "indexed_chunks": total_chunks,
                "failed_documents": failed_docs,
            }

            logger.info(
                f"Indexing complete: {processed_docs} documents, {total_chunks} chunks indexed"
            )

            return result

        except Exception as e:
            logger.error(f"Error in process_and_index_documents: {e}")
            raise

    async def generate_index_schema_json(self) -> Dict[str, Any]:
        """
        Generate the vector store schema as JSON for reference.

        Returns:
            Dictionary representing the vector store configuration
        """
        stats = await self.vector_store.get_stats()
        
        schema = {
            "type": "HNSW (Hierarchical Navigable Small World)",
            "dimension": 1536,
            "space": "cosine",
            "parameters": {
                "M": 16,
                "ef_construction": 200,
                "ef_search": 50,
                "max_elements": stats.get("max_elements", 10000),
            },
            "metadata_fields": [
                "id",
                "content",
                "filename",
                "page_number",
                "section_title",
                "chunk_index",
                "session_id",
                "file_type",
                "page_count",
            ],
            "stats": stats,
        }

        return schema

