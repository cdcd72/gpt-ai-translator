from dataclasses import dataclass
from config.base import BaseConfig
from typing import Optional
from minio import Minio


@dataclass
class MinioConfig(BaseConfig):
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str = None

    @classmethod
    def from_env(cls) -> "MinioConfig":
        return cls(
            endpoint=cls.get_required("MINIO_ENDPOINT"),
            access_key=cls.get_required("MINIO_ACCESS_KEY"),
            secret_key=cls.get_required("MINIO_SECRET_KEY"),
            bucket_name=cls.get_str("MINIO_BUCKET"),
        )

    @classmethod
    def merge(
        cls, base: "MinioConfig", override: Optional["MinioConfig"]
    ) -> "MinioConfig":
        if override is None:
            return base
        return cls(
            endpoint=override.endpoint or base.endpoint,
            access_key=override.access_key or base.access_key,
            secret_key=override.secret_key or base.secret_key,
            bucket_name=override.bucket_name or base.bucket_name,
        )


class MinioStorage:
    def __init__(self, config: Optional[MinioConfig] = None):
        self.config = MinioConfig.merge(base=MinioConfig.from_env(), override=config)
        self.client = Minio(
            self.config.endpoint,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
        )
        self.bucket_name = self.config.bucket_name

    def clean_files(
        self, bucket_name: str, prefix: str, recursive: bool = True
    ) -> None:
        bucket_name = self.resolve_bucket_name(bucket_name)
        objects = self.client.list_objects(bucket_name, prefix, recursive)
        for object in objects:
            self.client.remove_object(bucket_name, object.object_name)

    def upload_file(self, bucket_name: str, object_name: str, file_path: str) -> None:
        bucket_name = self.resolve_bucket_name(bucket_name)
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
        self.client.fput_object(bucket_name, object_name, file_path)

    def get_file_url(self, bucket_name: str, object_name: str) -> str:
        bucket_name = self.resolve_bucket_name(bucket_name)
        return self.client.presigned_get_object(bucket_name, object_name)

    def resolve_bucket_name(self, bucket_name: str) -> str:
        return self.bucket_name or bucket_name
