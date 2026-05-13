from __future__ import annotations

from datetime import timedelta

from minio import Minio

from app.core.config import get_settings
from app.integrations.errors import ObjectStorageError


class MinIOClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.minio_bucket
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=False,
        )

    def presigned_get_url(self, object_name: str, expires: timedelta | None = None) -> str:
        try:
            return self._client.presigned_get_object(
                self.bucket,
                object_name,
                expires=expires or timedelta(minutes=15),
            )
        except Exception as exc:
            raise ObjectStorageError(f"Unable to sign object {object_name}") from exc

    def get_object_text(self, object_name: str) -> bytes:
        try:
            response = self._client.get_object(self.bucket, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception as exc:
            raise ObjectStorageError(f"Unable to read object {object_name}") from exc
