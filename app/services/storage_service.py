"""
Local filesystem storage service for document storage.
"""
from typing import Optional, BinaryIO
from pathlib import Path
import os
import shutil
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Service for local filesystem document storage operations."""

    def __init__(self):
        """Initialize local filesystem storage."""
        # Base data directory (mounted or local)
        # Convert to absolute path if relative
        data_dir_str = settings.data_directory
        if not os.path.isabs(data_dir_str):
            # Make relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = (project_root / data_dir_str).resolve()
        else:
            self.data_dir = Path(data_dir_str).resolve()
        
        # Subdirectories
        self.source_dir = self.data_dir / "source"
        self.output_dir = self.data_dir / "output"
        self.archive_dir = self.data_dir / "archive"
        
        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_dir,
            self.source_dir,
            self.output_dir,
            self.archive_dir,
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {e}")
                raise

    async def upload_file(
        self,
        file_content: bytes | BinaryIO,
        file_name: str,
        subdirectory: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Save a file to local filesystem.

        Args:
            file_content: File content as bytes or file-like object
            file_name: Name for the file
            subdirectory: Subdirectory within source_dir (e.g., "session_1")
            content_type: MIME type of the file (not used, kept for compatibility)
            metadata: Optional metadata dictionary (not used, kept for compatibility)

        Returns:
            File path as string
        """
        try:
            # Determine target directory
            target_dir = self.source_dir
            if subdirectory:
                target_dir = target_dir / subdirectory
                target_dir.mkdir(parents=True, exist_ok=True)

            # Full file path
            file_path = target_dir / file_name

            # Write file
            if isinstance(file_content, bytes):
                file_path.write_bytes(file_content)
            else:
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file_content, f)

            file_path_str = str(file_path)
            logger.info(f"Saved file: {file_name} to {file_path_str}")

            return file_path_str

        except Exception as e:
            logger.error(f"Error saving file {file_name}: {e}")
            raise

    async def download_file(
        self,
        file_path: str,
        subdirectory: Optional[str] = None,
    ) -> bytes:
        """
        Read a file from local filesystem.

        Args:
            file_path: Path to the file (relative to source_dir or absolute)
            subdirectory: Optional subdirectory (if file_path is relative)

        Returns:
            File content as bytes
        """
        try:
            # Handle absolute vs relative paths
            if os.path.isabs(file_path):
                path = Path(file_path)
            else:
                target_dir = self.source_dir
                if subdirectory:
                    target_dir = target_dir / subdirectory
                path = target_dir / file_path

            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            file_content = path.read_bytes()
            logger.info(f"Read file: {path}")
            return file_content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    async def delete_file(
        self,
        file_path: str,
        subdirectory: Optional[str] = None,
    ) -> bool:
        """
        Delete a file from local filesystem.

        Args:
            file_path: Path to the file (relative to source_dir or absolute)
            subdirectory: Optional subdirectory (if file_path is relative)

        Returns:
            True if successful
        """
        try:
            # Handle absolute vs relative paths
            if os.path.isabs(file_path):
                path = Path(file_path)
            else:
                target_dir = self.source_dir
                if subdirectory:
                    target_dir = target_dir / subdirectory
                path = target_dir / file_path

            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {path}")
            else:
                logger.warning(f"File not found for deletion: {path}")

            return True

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise

    async def list_files(
        self,
        subdirectory: Optional[str] = None,
        prefix: Optional[str] = None,
        extensions: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        List files in the data directory.

        Args:
            subdirectory: Optional subdirectory to search (e.g., "session_1")
            prefix: Optional prefix filter for filenames
            extensions: Optional list of file extensions to filter (e.g., [".pdf", ".docx"])

        Returns:
            List of file information dictionaries
        """
        try:
            target_dir = self.data_dir
            if subdirectory:
                target_dir = target_dir / subdirectory

            if not target_dir.exists():
                logger.warning(f"Directory does not exist: {target_dir}")
                return []

            file_list = []
            # Use glob for root level, rglob for recursive
            if subdirectory:
                # Recursive search in subdirectory
                search_pattern = "**/*"
            else:
                # Only root level files (not in subdirectories)
                search_pattern = "*"
            
            for file_path in target_dir.glob(search_pattern):
                if file_path.is_file():
                    # Filter by prefix
                    if prefix and not file_path.name.startswith(prefix):
                        continue
                    
                    # Filter by extension
                    if extensions and file_path.suffix.lower() not in extensions:
                        continue

                    stat = file_path.stat()
                    file_list.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.data_dir)),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": file_path.suffix.lower(),
                    })

            logger.info(f"Listed {len(file_list)} files from {target_dir}")
            return file_list

        except Exception as e:
            logger.error(f"Error listing files in {target_dir}: {e}")
            raise

    async def move_to_archive(
        self,
        file_path: str,
        subdirectory: Optional[str] = None,
    ) -> str:
        """
        Move a file to the archive directory.

        Args:
            file_path: Path to the file (relative to source_dir or absolute)
            subdirectory: Optional subdirectory (if file_path is relative)

        Returns:
            Path of archived file
        """
        try:
            # Get source path
            if os.path.isabs(file_path):
                source_path = Path(file_path)
            else:
                target_dir = self.source_dir
                if subdirectory:
                    target_dir = target_dir / subdirectory
                source_path = target_dir / file_path

            if not source_path.exists():
                raise FileNotFoundError(f"File not found: {source_path}")

            # Create archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_filename = f"{timestamp}_{source_path.name}"
            archive_path = self.archive_dir / archive_filename

            # Move file
            shutil.move(str(source_path), str(archive_path))

            logger.info(f"Moved {source_path} to archive: {archive_path}")
            return str(archive_path)

        except Exception as e:
            logger.error(f"Error moving file {file_path} to archive: {e}")
            raise

    def get_file_path(
        self,
        file_name: str,
        subdirectory: Optional[str] = None,
    ) -> str:
        """
        Get the full path for a file.

        Args:
            file_name: Name of the file
            subdirectory: Optional subdirectory

        Returns:
            Full file path
        """
        target_dir = self.source_dir
        if subdirectory:
            target_dir = target_dir / subdirectory
        return str(target_dir / file_name)
