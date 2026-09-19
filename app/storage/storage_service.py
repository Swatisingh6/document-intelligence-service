import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from app.core.config import settings


class StorageProvider(ABC):
    """Abstract interface for document file storage."""

    @abstractmethod
    def save_file(self, content: bytes, original_filename: str) -> str:
        """Save file bytes and return a unique storage key/path."""
        pass

    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        """Get absolute local filesystem path for a storage key."""
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """Delete file associated with storage key."""
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation with path traversal protection."""

    def __init__(self, base_dir: str = settings.STORAGE_PATH):
        self.base_path = Path(base_dir).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _safe_resolve(self, storage_key: str) -> Path:
        """Resolve path and verify it stays within base_path (prevents path traversal)."""
        target_path = (self.base_path / storage_key).resolve()
        if not str(target_path).startswith(str(self.base_path)):
            raise ValueError(f"Security error: Path traversal attempt detected for '{storage_key}'")
        return target_path

    def save_file(self, content: bytes, original_filename: str) -> str:
        ext = Path(original_filename).suffix.lower()
        if not ext:
            ext = ".bin"
        safe_filename = f"{uuid.uuid4()}{ext}"
        target_path = self._safe_resolve(safe_filename)

        with open(target_path, "wb") as f:
            f.write(content)

        return safe_filename

    def get_file_path(self, storage_key: str) -> str:
        target_path = self._safe_resolve(storage_key)
        if not target_path.exists():
            raise FileNotFoundError(f"Storage file '{storage_key}' not found.")
        return str(target_path)

    def delete_file(self, storage_key: str) -> bool:
        try:
            target_path = self._safe_resolve(storage_key)
            if target_path.exists():
                target_path.unlink()
                return True
        except Exception:
            pass
        return False

    def exists(self, storage_key: str) -> bool:
        try:
            target_path = self._safe_resolve(storage_key)
            return target_path.exists()
        except Exception:
            return False


# Singleton storage instance
storage_service = LocalStorageProvider()
