from dataclasses import dataclass
from config.base import BaseConfig
from typing import Optional
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ShowLoadingAnimationRequest,
    ReplyMessageRequest,
    PushMessageRequest,
)


@dataclass
class LineConfig(BaseConfig):
    access_token: str
    channel_secret: str

    @classmethod
    def from_env(cls) -> "LineConfig":
        return cls(
            access_token=cls.get_required("LINE_CHANNEL_ACCESS_TOKEN"),
            channel_secret=cls.get_required("LINE_CHANNEL_SECRET"),
        )


class Line:
    def __init__(self, config: Optional[LineConfig] = None):
        self.config = config or LineConfig.from_env()
        self.configuration = Configuration(access_token=self.config.access_token)
        self.handler = WebhookHandler(self.config.channel_secret)

    def show_loading_animation(self, chat_id: str) -> None:
        with ApiClient(self.configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.show_loading_animation(
                ShowLoadingAnimationRequest(chatId=chat_id, loadingSeconds=60),
            )

    def write_audio_by_message(self, message_id: str, audio_path: str) -> None:
        with ApiClient(self.configuration) as api_client:
            messaging_blob_api = MessagingApiBlob(api_client)
            with open(audio_path, "wb") as audio_file:
                audio_file.write(
                    messaging_blob_api.get_message_content(message_id=message_id)
                )

    def reply_message(self, reply_token: str, message) -> None:
        with ApiClient(self.configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                ReplyMessageRequest(reply_token=reply_token, messages=[message]),
            )

    def push_message(self, chat_id: str, message) -> None:
        with ApiClient(self.configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.push_message(
                PushMessageRequest(to=chat_id, messages=[message]),
            )
