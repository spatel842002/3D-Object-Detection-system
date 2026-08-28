"""Object storage abstraction: local filesystem (tests/offline) or S3-compatible (MinIO/AWS S3)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO, Protocol


class ObjectStorage(Protocol):
    def put(self, key: str, data: BinaryIO) -> str: ...

    def get_path_or_url(self, key: str) -> str: ...

    def exists(self, key: str) -> bool: ...


class LocalFilesystemStorage:
    """Filesystem-backed storage used for local development and unit tests."""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, data: BinaryIO) -> str:
        destination = self._base_dir / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as fh:
            shutil.copyfileobj(data, fh)
        return str(destination)

    def get_path_or_url(self, key: str) -> str:
        return str(self._base_dir / key)

    def exists(self, key: str) -> bool:
        return (self._base_dir / key).exists()


class S3CompatibleStorage:
    """S3-compatible storage: works against MinIO locally and AWS S3 in production.

    Selected by STORAGE_BACKEND=s3. See docs/environment-variables.md for the
    full S3_* contract and docs/account-activation-checklist.md for bucket
    bootstrap in a real AWS account.
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str,
        use_ssl: bool,
    ) -> None:
        import boto3

        self._bucket = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            use_ssl=use_ssl,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        from botocore.exceptions import ClientError

        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)

    def put(self, key: str, data: BinaryIO) -> str:
        self._client.upload_fileobj(data, self._bucket, key)
        return f"s3://{self._bucket}/{key}"

    def get_path_or_url(self, key: str) -> str:
        return self._client.generate_presigned_url(
            "get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=3600
        )

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False


def build_storage_from_settings(settings) -> ObjectStorage:  # noqa: ANN001 - avoids import cycle
    if settings.storage_backend == "s3":
        return S3CompatibleStorage(
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket_name=settings.s3_bucket_name,
            region=settings.s3_region,
            use_ssl=settings.s3_use_ssl,
        )
    return LocalFilesystemStorage(settings.local_storage_dir)
