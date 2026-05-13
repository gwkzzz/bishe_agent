from __future__ import annotations

from datetime import timedelta
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

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

    def ensure_bucket(self) -> None:
        try:
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket)
        except Exception as exc:
            raise ObjectStorageError(f"Unable to ensure MinIO bucket {self.bucket}") from exc

    def put_object(
        self,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        try:
            self.ensure_bucket()
            self._client.put_object(
                self.bucket,
                object_name,
                data,
                length,
                content_type=content_type,
            )
            return f"minio://{self.bucket}/{object_name}"
        except Exception as exc:
            raise ObjectStorageError(f"Unable to upload object {object_name}") from exc

    def presigned_get_url(self, object_name: str, expires: timedelta | None = None) -> str:
        try:
            return self._client.presigned_get_object(
                self.bucket,
                object_name,
                expires=expires or timedelta(minutes=15),
            )
        except Exception as exc:
            raise ObjectStorageError(f"Unable to sign object {object_name}") from exc

    def get_object_bytes(self, object_name: str) -> bytes:
        response = None
        try:
            response = self._client.get_object(self.bucket, object_name)
            return response.read()
        except S3Error as exc:
            raise ObjectStorageError(f"Unable to read object {object_name}") from exc
        except Exception as exc:
            raise ObjectStorageError(f"Unable to read object {object_name}") from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()
