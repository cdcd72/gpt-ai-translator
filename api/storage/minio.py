import os

from dataclasses import dataclass
from dotenv import load_dotenv
from minio import Minio

load_dotenv()


@dataclass
class MinioConfig:
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str

    @classmethod
    def from_env(cls) -> "MinioConfig":
        return cls(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            bucket_name=os.getenv("MINIO_BUCKET"),
        )


class MinioStorage:
    def __init__(self, config: MinioConfig = MinioConfig.from_env()):
        self.client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
        )
        self.bucket_name = config.bucket_name

    def clean_files(self, bucket_name, prefix, recursive):
        bucket_name = self.resolve_bucket_name(bucket_name)
        objects = self.client.list_objects(bucket_name, prefix, recursive)
        for object in objects:
            self.client.remove_object(bucket_name, object.object_name)

    def upload_file(self, bucket_name, object_name, file_path):
        bucket_name = self.resolve_bucket_name(bucket_name)
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
        self.client.fput_object(bucket_name, object_name, file_path)

    def get_file_url(self, bucket_name, object_name):
        bucket_name = self.resolve_bucket_name(bucket_name)
        return self.client.presigned_get_object(bucket_name, object_name)

    def resolve_bucket_name(self, bucket_name):
        return self.bucket_name or bucket_name
