import os
import hashlib

from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ShowLoadingAnimationRequest,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    AudioMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, AudioMessageContent
from gtts import gTTS
from api.ai.chatgpt import ChatGPT
from api.config.configs import *
from api.storage.minio import MinioStorage
from api.media.ffmpeg import FFmpeg

load_dotenv()

app = Flask(__name__)
environment = Environment[os.getenv("APP_ENVIRONMENT", Environment.VERCEL.value)]
if environment == Environment.DEVELOPMENT:
    app.config.from_object(DevelopmentConfig)
elif environment == Environment.PRODUCTION:
    app.config.from_object(ProductionConfig)
elif environment == Environment.VERCEL:
    app.config.from_object(ProductionForVercelConfig)

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

push_translated_text_audio_enabled = (
    os.getenv("APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED", "false") == "true"
)

chatgpt = ChatGPT()
minio_storage = MinioStorage() if push_translated_text_audio_enabled else None
ffmpeg = FFmpeg() if push_translated_text_audio_enabled else None

# region Language related

lang_dict = {
    "繁體中文": "Traditional Chinese",
    "簡體中文": "Simplified Chinese",
    "英文": "English",
    "日文": "Japanese",
    "韓文": "Korean",
    "越南文": "Vietnamese",
    "泰文": "Thai",
    "義大利文": "Italian",
    "西班牙文": "Spanish",
    "葡萄牙文": "Portuguese",
    "荷蘭文": "Dutch",
    "德文": "German",
    "法文": "French",
}
reverse_lang_dict = {value: key for key, value in lang_dict.items()}
# IETF language tag
ietf_lang_dict = {
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh-CN",
    "English": "en",
    "Japanese": "ja",
    "Korean": "ko",
    "Vietnamese": "vi",
    "Thai": "th",
    "Italian": "it",
    "Spanish": "es",
    "Portuguese": "pt",
    "Dutch": "nl",
    "German": "de",
    "French": "fr",
}

# endregion

# region User related

user_translate_language_key = "translate_language"
user_audio_language_key = "audio_language"

user_dict = {}

# endregion


@app.route("/")
def home():
    return "OK"


@app.route("/webhook", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    user_input = event.message.text
    if (user_input == "/setting") or (user_input == "設定"):
        flex_message = TextMessage(
            text="請選擇語音辨識後的翻譯語言（我方語言）",
            quick_reply=QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(
                            label="繁體中文", text="設定辨識翻譯 " + "繁體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="簡體中文", text="設定辨識翻譯 " + "簡體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="英文", text="設定辨識翻譯 " + "英文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="日文", text="設定辨識翻譯 " + "日文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="韓文", text="設定辨識翻譯 " + "韓文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="越南文", text="設定辨識翻譯 " + "越南文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="泰文", text="設定辨識翻譯 " + "泰文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="義大利文", text="設定辨識翻譯 " + "義大利文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="西班牙文", text="設定辨識翻譯 " + "西班牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="葡萄牙文", text="設定辨識翻譯 " + "葡萄牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="荷蘭文", text="設定辨識翻譯 " + "荷蘭文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="德文", text="設定辨識翻譯 " + "德文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="法文", text="設定辨識翻譯 " + "法文"
                        )
                    ),
                ]
            ),
        )
        reply_message(event.reply_token, flex_message)

    elif "設定辨識翻譯" in user_input:
        # Set audio language by user
        user_dict[user_id][user_audio_language_key] = lang_dict[
            user_input.split(" ")[1]
        ]
        flex_message = TextMessage(
            text="請選擇打字後的翻譯語言（對方語言）",
            quick_reply=QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(
                            label="繁體中文", text="設定打字翻譯 " + "繁體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="簡體中文", text="設定打字翻譯 " + "簡體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="英文", text="設定打字翻譯 " + "英文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="日文", text="設定打字翻譯 " + "日文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="韓文", text="設定打字翻譯 " + "韓文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="越南文", text="設定打字翻譯 " + "越南文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="泰文", text="設定打字翻譯 " + "泰文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="義大利文", text="設定打字翻譯 " + "義大利文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="西班牙文", text="設定打字翻譯 " + "西班牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="葡萄牙文", text="設定打字翻譯 " + "葡萄牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="荷蘭文", text="設定打字翻譯 " + "荷蘭文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="德文", text="設定打字翻譯 " + "德文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="法文", text="設定打字翻譯 " + "法文"
                        )
                    ),
                ]
            ),
        )
        reply_message(event.reply_token, flex_message)

    elif "設定打字翻譯" in user_input:
        # Set translate language by user
        user_dict[user_id][user_translate_language_key] = lang_dict[
            user_input.split(" ")[1]
        ]
        # Format response message
        audio_language = user_dict[user_id][user_audio_language_key]
        translate_language = user_dict[user_id][user_translate_language_key]
        response_text = f"""設定完畢！
我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        reply_message(event.reply_token, TextMessage(text=response_text))

    elif (user_input == "/current-setting") or (user_input == "目前設定"):
        # Format response message
        audio_language = user_dict[user_id][user_audio_language_key]
        translate_language = user_dict[user_id][user_translate_language_key]
        response_text = f"""我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        reply_message(event.reply_token, TextMessage(text=response_text))

    else:
        # Show loading animation
        show_loading_animation(user_id)
        # Translate text from user input
        translated_text = chatgpt.translate(
            user_input, user_dict[user_id][user_translate_language_key]
        )
        # Reply translated text
        reply_message(event.reply_token, TextMessage(text=translated_text))
        if push_translated_text_audio_enabled:
            translated_text_audio_path = os.path.join(
                app.config.get("AUDIO_TEMP_PATH"), f"{event.message.id}.m4a"
            )
            # Convert translated text to audio file
            tts = gTTS(
                translated_text,
                lang=ietf_lang_dict[user_dict[user_id][user_translate_language_key]],
            )
            tts.save(translated_text_audio_path)
            # Operate audio file with remote storage
            clean_audios(user_id)
            upload_audio(user_id, translated_text_audio_path)
            translated_text_audio_url = get_audio_url(
                user_id, translated_text_audio_path
            )
            translated_text_audio_duration = (
                get_audio_duration(translated_text_audio_path) * 1000
            )
            # Push audio message from audio file
            push_message(
                user_id,
                AudioMessage(
                    originalContentUrl=translated_text_audio_url,
                    duration=int(translated_text_audio_duration),
                ),
            )


@line_handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    # Show loading animation
    show_loading_animation(user_id)
    # Read audio message for whisper api input
    user_audio_path = write_audio_message(event.message.id)
    whispered_text = chatgpt.whisper(user_audio_path)
    if os.path.exists(user_audio_path):
        os.remove(user_audio_path)
    # Translate text from whisper api output
    translated_text = chatgpt.translate(
        whispered_text, user_dict[user_id][user_audio_language_key]
    )
    # Reply translated text
    reply_message(event.reply_token, TextMessage(text=translated_text))


def user_exists(user_id):
    return user_id in user_dict


def init_user_lang(user_id):
    user_dict[user_id] = {
        user_translate_language_key: "English",
        user_audio_language_key: "Traditional Chinese",
    }


def clean_audios(user_id):
    minio_storage.clean_files(
        "gpt-ai-translator", hashlib.sha256(user_id.encode()).hexdigest(), True
    )


def upload_audio(user_id, audio_path):
    minio_storage.upload_file(
        "gpt-ai-translator",
        f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}",
        audio_path,
    )


def get_audio_url(user_id, audio_path):
    return minio_storage.get_file_url(
        "gpt-ai-translator",
        f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}",
    )


def get_audio_duration(audio_path):
    return ffmpeg.probe(audio_path)["format"]["duration"]


def show_loading_animation(chat_id):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(chatId=chat_id, loadingSeconds=60),
        )


def write_audio_message(message_id):
    audio_path = os.path.join(app.config.get("AUDIO_TEMP_PATH"), f"{message_id}.m4a")
    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
        with open(audio_path, "wb") as audio_file:
            audio_file.write(
                line_bot_blob_api.get_message_content(message_id=message_id)
            )
    return audio_path


def reply_message(reply_token, message):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[message]),
        )


def push_message(chat_id, message):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(to=chat_id, messages=[message]),
        )


if __name__ == "__main__":
    app.run()
