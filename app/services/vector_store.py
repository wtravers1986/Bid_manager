"""
Local HNSW vector store for semantic search using hnswlib.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os
import numpy as np
import hnswlib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Local HNSW vector store for semantic search."""

    def __init__(self, dimension: int = 1536):
        """
        Initialize HNSW vector store.

        Args:
            dimension: Dimension of embedding vectors (default: 1536 for ada-002)
        """
        self.dimension = dimension
        
        # Resolve data directory path
        data_dir_str = settings.data_directory
        if not os.path.isabs(data_dir_str):
            # Make relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = (project_root / data_dir_str).resolve()
        else:
            self.data_dir = Path(data_dir_str).resolve()
        
        self.index_path = self.data_dir / "vector_index.bin"
        self.metadata_path = self.data_dir / "vector_metadata.json"
        
        # HNSW index
        self.index: Optional[hnswlib.Index] = None
        
        # Metadata storage: {id: {content, filename, page_number, ...}}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # ID to index mapping
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.next_index = 0
        
        # Load existing index if available
        self._load_index()

    def _load_index(self) -> None:
        """Load existing index and metadata from disk."""
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            if self.index_path.exists() and self.metadata_path.exists():
                # Load metadata
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = data.get('metadata', {})
                    self.id_to_index = data.get('id_to_index', {})
                    self.index_to_id = {v: k for k, v in self.id_to_index.items()}
                    self.next_index = data.get('next_index', len(self.id_to_index))
                
                # Load HNSW index
                self.index = hnswlib.Index(space='cosine', dim=self.dimension)
                self.index.load_index(str(self.index_path))
                
                # Set ef parameter for search
                self.index.set_ef(50)
                
                logger.info(
                    f"Loaded vector index with {len(self.metadata)} vectors from {self.index_path}"
                )
            else:
                # Create new index
                self._create_new_index()
                logger.info("Created new vector index")
        except Exception as e:
            logger.warning(f"Error loading index, creating new one: {e}")
            self._create_new_index()

    def _create_new_index(self) -> None:
        """Create a new HNSW index."""
        # Initialize HNSW index
        # max_elements: maximum number of elements (can be increased)
        # ef_construction: controls index search speed/build speed tradeoff
        # M: number of bi-directional links (higher = more accurate, slower)
        max_elements = 10000  # Can be increased later
        ef_construction = 200
        M = 16
        
        self.index = hnswlib.Index(space='cosine', dim=self.dimension)
        self.index.init_index(max_elements=max_elements, ef_construction=ef_construction, M=M)
        self.index.set_ef(50)  # ef should be > k for search
        
        self.metadata = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_index = 0

    def _save_index(self) -> None:
        """Save index and metadata to disk."""
        try:
            # Ensure directory exists
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save HNSW index
            if self.index is not None:
                self.index.save_index(str(self.index_path))
            
            # Save metadata
            data = {
                'metadata': self.metadata,
                'id_to_index': self.id_to_index,
                'next_index': self.next_index,
            }
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved vector index to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

    async def add_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata_list: List[Dict[str, Any]],
    ) -> int:
        """
        Add vectors to the index.

        Args:
            vectors: List of embedding vectors
            ids: List of unique IDs for each vector
            metadata_list: List of metadata dictionaries for each vector

        Returns:
            Number of vectors added
        """
        if not vectors or not ids:
            return 0

        if len(vectors) != len(ids) or len(vectors) != len(metadata_list):
            raise ValueError("vectors, ids, and metadata_list must have same length")

        try:
            # Convert to numpy array
            vectors_array = np.array(vectors, dtype=np.float32)

            # Check if index needs to be resized
            current_max = self.index.get_max_elements()
            needed_size = self.next_index + len(vectors)
            
            if needed_size > current_max:
                # Resize index (can only grow, not shrink)
                new_size = max(current_max * 2, needed_size)
                self.index.resize_index(new_size)
                logger.info(f"Resized index to {new_size} elements")

            # Add vectors to index
            start_idx = self.next_index
            self.index.add_items(vectors_array, np.arange(start_idx, start_idx + len(vectors)))

            # Store metadata and mappings
            for idx, (vector_id, metadata) in enumerate(zip(ids, metadata_list)):
                internal_idx = start_idx + idx
                self.id_to_index[vector_id] = internal_idx
                self.index_to_id[internal_idx] = vector_id
                self.metadata[vector_id] = metadata

            self.next_index += len(vectors)

            # Save to disk
            self._save_index()

            logger.info(f"Added {len(vectors)} vectors to index")
            return len(vectors)

        except Exception as e:
            logger.error(f"Error adding vectors: {e}")
            raise

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters (e.g., {"filename": "doc.pdf"})

        Returns:
            List of search results with metadata
        """
        if self.index is None or len(self.metadata) == 0:
            return []

        try:
            # Convert query to numpy array
            query_array = np.array([query_vector], dtype=np.float32)

            # Search in index
            # Returns (labels, distances) where labels are internal indices
            labels, distances = self.index.knn_query(query_array, k=min(top_k * 2, len(self.metadata)))

            # Convert internal indices to IDs and apply filters
            results = []
            for label, distance in zip(labels[0], distances[0]):
                internal_idx = int(label)
                
                if internal_idx not in self.index_to_id:
                    continue
                
                vector_id = self.index_to_id[internal_idx]
                metadata = self.metadata.get(vector_id, {}).copy()
                
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if metadata.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # Add similarity score (1 - distance for cosine similarity)
                metadata['id'] = vector_id
                metadata['score'] = float(1.0 - distance)  # Cosine distance to similarity
                metadata['distance'] = float(distance)
                
                results.append(metadata)
                
                if len(results) >= top_k:
                    break

            logger.debug(f"Search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise

    async def delete_by_ids(self, ids: List[str]) -> int:
        """
        Delete vectors by IDs.

        Note: HNSW doesn't support deletion efficiently, so we mark as deleted.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted
        """
        deleted = 0
        for vector_id in ids:
            if vector_id in self.metadata:
                # Mark as deleted (remove from metadata)
                del self.metadata[vector_id]
                if vector_id in self.id_to_index:
                    internal_idx = self.id_to_index[vector_id]
                    del self.id_to_index[vector_id]
                    if internal_idx in self.index_to_id:
                        del self.index_to_id[internal_idx]
                deleted += 1

        if deleted > 0:
            self._save_index()
            logger.info(f"Deleted {deleted} vectors from index")

        return deleted

    def is_empty(self) -> bool:
        """
        Check if the index is empty (has no vectors).
        
        Returns:
            True if index is empty, False otherwise
        """
        return len(self.metadata) == 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_vectors": len(self.metadata),
            "dimension": self.dimension,
            "max_elements": self.index.get_max_elements() if self.index else 0,
            "current_count": self.next_index,
            "index_path": str(self.index_path),
        }

    async def clear(self) -> bool:
        """Clear all vectors from the index."""
        try:
            self._create_new_index()
            # Delete files
            if self.index_path.exists():
                self.index_path.unlink()
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            logger.info("Cleared vector index")
            return True
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            raise

