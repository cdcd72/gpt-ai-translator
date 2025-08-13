import os

from dotenv import load_dotenv
from minio import Minio

load_dotenv()


class MinioStorage:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
        )
        self.bucket_name = os.getenv("MINIO_BUCKET")

    def clean_files(self, bucket_name, prefix, recursive):
        bucket_name = self.bucket_name or bucket_name
        objects = self.client.list_objects(bucket_name, prefix, recursive)
        for object in objects:
            self.client.remove_object(bucket_name, object.object_name)

    def upload_file(self, bucket_name, object_name, file_path):
        bucket_name = self.bucket_name or bucket_name
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
        self.client.fput_object(bucket_name, object_name, file_path)

    def get_file_url(self, bucket_name, object_name):
        bucket_name = self.bucket_name or bucket_name
        return self.client.presigned_get_object(bucket_name, object_name)
