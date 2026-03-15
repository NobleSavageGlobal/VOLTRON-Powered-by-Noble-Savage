from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles

from app.config import settings
from app.core.exceptions import StorageError


class StorageService(ABC):
    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """Save content and return storage path."""

    @abstractmethod
    async def load(self, filename: str) -> bytes:
        """Load content by filename."""

    @abstractmethod
    async def delete(self, filename: str) -> None:
        """Delete a stored file."""

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Get a URL or path for the stored file."""


class LocalStorageService(StorageService):
    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        file_path = self.base_path / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path)

    async def load(self, filename: str) -> bytes:
        file_path = self.base_path / filename
        if not file_path.exists():
            raise StorageError(f"File not found: {filename}")
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, filename: str) -> None:
        file_path = self.base_path / filename
        if file_path.exists():
            os.remove(file_path)

    def get_url(self, filename: str) -> str:
        return str(self.base_path / filename)


class S3StorageService(StorageService):
    def __init__(self) -> None:
        self.bucket = settings.S3_BUCKET
        self.region = settings.AWS_REGION
        self._client = None

    def _get_client(self):  # type: ignore[return]
        if self._client is None:
            import boto3
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.region,
            )
        return self._client

    async def save(self, filename: str, content: bytes) -> str:
        import asyncio
        client = self._get_client()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.put_object(Bucket=self.bucket, Key=filename, Body=content),
        )
        return filename

    async def load(self, filename: str) -> bytes:
        import asyncio
        client = self._get_client()
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.get_object(Bucket=self.bucket, Key=filename),
        )
        return response["Body"].read()

    async def delete(self, filename: str) -> None:
        import asyncio
        client = self._get_client()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.delete_object(Bucket=self.bucket, Key=filename),
        )

    def get_url(self, filename: str) -> str:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{filename}"


def get_storage_service() -> StorageService:
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageService()
    return LocalStorageService()
