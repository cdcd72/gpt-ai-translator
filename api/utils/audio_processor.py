import os
import hashlib
from storage.minio import MinioStorage
from media.tinytag import TinyTagMedia


class AudioProcessor:
    def __init__(
        self,
        minio_storage: MinioStorage | None,
        tinytag_media: TinyTagMedia | None,
        app_name: str,
    ):
        self.minio_storage = minio_storage
        self.tinytag_media = tinytag_media
        self.app_name = app_name

    def clean_audios(self, user_id: str) -> None:
        if self.minio_storage:
            bucket_name = self.app_name
            self.minio_storage.clean_files(
                bucket_name, hashlib.sha256(user_id.encode()).hexdigest()
            )

    def upload_audio(self, user_id: str, audio_path: str) -> None:
        if self.minio_storage:
            bucket_name = self.app_name
            self.minio_storage.upload_file(
                bucket_name,
                f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}",
                audio_path,
            )

    def get_audio_url(self, user_id: str, audio_path: str) -> str:
        if self.minio_storage:
            bucket_name = self.app_name
            return self.minio_storage.get_file_url(
                bucket_name,
                f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}",
            )
        return ""

    def get_audio_duration(self, audio_path: str) -> float:
        if self.tinytag_media:
            return self.tinytag_media.get_audio_duration(audio_path)
        return 0.0
