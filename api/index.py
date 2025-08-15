import os
import hashlib
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    TextMessage,
    AudioMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, AudioMessageContent
from api.bot.line import Line
from api.ai.chatgpt import ChatGPT
from api.config.base import BaseConfig
from api.config.configs import *
from api.storage.cache import CacheConfig, MultiTierCacheAdapter
from api.storage.minio import MinioStorage
from api.media.tinytag import TinyTagMedia

load_dotenv()

app = Flask(__name__)
environment = Environment[
    BaseConfig.get_str("APP_ENVIRONMENT", Environment.VERCEL.value)
]
if environment == Environment.DEVELOPMENT:
    app.config.from_object(DevelopmentConfig)
elif environment == Environment.PRODUCTION:
    app.config.from_object(ProductionConfig)
elif environment == Environment.VERCEL:
    app.config.from_object(ProductionForVercelConfig)
name = BaseConfig.get_str("APP_NAME", "gpt-ai-translator")
persistent_user_settings_enabled = BaseConfig.get_bool(
    "APP_PERSISTENT_USER_SETTINGS_ENABLED", False
)
push_translated_text_audio_enabled = BaseConfig.get_bool(
    "APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED", False
)

line = Line()
chatgpt = ChatGPT()
minio_storage = MinioStorage() if push_translated_text_audio_enabled else None
tinytag_media = TinyTagMedia() if push_translated_text_audio_enabled else None

# region Language related

lang_dict = {
    "繁體中文": "Traditional Chinese",
    "簡體中文": "Simplified Chinese",
    "英文": "English",
    "日文": "Japanese",
    "韓文": "Korean",
    "越南文": "Vietnamese",
    "泰文": "Thai",
    "印尼文": "Indonesian",
    "義大利文": "Italian",
    "西班牙文": "Spanish",
    "葡萄牙文": "Portuguese",
    "德文": "German",
    "法文": "French",
}
reverse_lang_dict = {value: key for key, value in lang_dict.items()}

# endregion

# region User related

user_translate_language_key = "translate_language"
user_audio_language_key = "audio_language"

user_settings_cache = MultiTierCacheAdapter(
    CacheConfig(remote_cache_enabled=persistent_user_settings_enabled)
)

# endregion


@app.route("/")
def home():
    return "OK"


@app.route("/webhook", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        line.handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@line.handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    user_input = event.message.text
    if (user_input == "/setting") or (user_input == "設定"):
        flex_message = TextMessage(
            text="請選擇我方使用語言",
            quick_reply=QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(
                            label="繁體中文", text="設定語音辨識後翻譯為 " + "繁體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="簡體中文", text="設定語音辨識後翻譯為 " + "簡體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="英文", text="設定語音辨識後翻譯為 " + "英文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="日文", text="設定語音辨識後翻譯為 " + "日文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="韓文", text="設定語音辨識後翻譯為 " + "韓文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="越南文", text="設定語音辨識後翻譯為 " + "越南文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="泰文", text="設定語音辨識後翻譯為 " + "泰文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="印尼文", text="設定語音辨識後翻譯為 " + "印尼文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="義大利文", text="設定語音辨識後翻譯為 " + "義大利文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="西班牙文", text="設定語音辨識後翻譯為 " + "西班牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="葡萄牙文", text="設定語音辨識後翻譯為 " + "葡萄牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="德文", text="設定語音辨識後翻譯為 " + "德文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="法文", text="設定語音辨識後翻譯為 " + "法文"
                        )
                    ),
                ]
            ),
        )
        line.reply_message(event.reply_token, flex_message)

    elif "設定語音辨識後翻譯為" in user_input:
        # Set audio language by user
        update_user_settings(
            user_id, {user_audio_language_key: lang_dict[user_input.split(" ")[1]]}
        )
        flex_message = TextMessage(
            text="請選擇對方使用語言",
            quick_reply=QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(
                            label="繁體中文", text="設定打字後翻譯為 " + "繁體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="簡體中文", text="設定打字後翻譯為 " + "簡體中文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="英文", text="設定打字後翻譯為 " + "英文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="日文", text="設定打字後翻譯為 " + "日文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="韓文", text="設定打字後翻譯為 " + "韓文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="越南文", text="設定打字後翻譯為 " + "越南文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="泰文", text="設定打字後翻譯為 " + "泰文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="印尼文", text="設定打字後翻譯為 " + "印尼文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="義大利文", text="設定打字後翻譯為 " + "義大利文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="西班牙文", text="設定打字後翻譯為 " + "西班牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="葡萄牙文", text="設定打字後翻譯為 " + "葡萄牙文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="德文", text="設定打字後翻譯為 " + "德文"
                        )
                    ),
                    QuickReplyItem(
                        action=MessageAction(
                            label="法文", text="設定打字後翻譯為 " + "法文"
                        )
                    ),
                ]
            ),
        )
        line.reply_message(event.reply_token, flex_message)

    elif "設定打字後翻譯為" in user_input:
        # Set translate language by user
        update_user_settings(
            user_id, {user_translate_language_key: lang_dict[user_input.split(" ")[1]]}
        )
        # Format response message
        user_settings = get_user_settings(user_id)
        audio_language = user_settings[user_audio_language_key]
        translate_language = user_settings[user_translate_language_key]
        response_text = f"""設定完畢！
我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line.reply_message(event.reply_token, TextMessage(text=response_text))

    elif (user_input == "/current-setting") or (user_input == "目前設定"):
        # Format response message
        user_settings = get_user_settings(user_id)
        audio_language = user_settings[user_audio_language_key]
        translate_language = user_settings[user_translate_language_key]
        response_text = f"""我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line.reply_message(event.reply_token, TextMessage(text=response_text))

    else:
        # Show loading animation
        line.show_loading_animation(user_id)
        # Translate text from user input
        user_settings = get_user_settings(user_id)
        translated_text = chatgpt.translate(
            user_input, user_settings[user_translate_language_key]
        )
        # Reply translated text
        line.reply_message(event.reply_token, TextMessage(text=translated_text))
        if push_translated_text_audio_enabled:
            translated_text_audio_path = os.path.join(
                app.config.get("AUDIO_TEMP_PATH"), f"{event.message.id}.mp3"
            )
            # Convert translated text to audio file
            chatgpt.tts(translated_text, translated_text_audio_path)
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
            line.push_message(
                user_id,
                AudioMessage(
                    originalContentUrl=translated_text_audio_url,
                    duration=int(translated_text_audio_duration),
                ),
            )


@line.handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    message_id = event.message.id
    # Show loading animation
    line.show_loading_animation(user_id)
    # Read audio message for whisper api input
    user_audio_path = os.path.join(
        app.config.get("AUDIO_TEMP_PATH"), f"{message_id}.m4a"
    )
    line.write_audio_by_message(message_id, user_audio_path)
    whispered_text = chatgpt.whisper(user_audio_path)
    if os.path.exists(user_audio_path):
        os.remove(user_audio_path)
    # Translate text from whisper api output
    user_settings = get_user_settings(user_id)
    translated_text = chatgpt.translate(
        whispered_text, user_settings[user_audio_language_key]
    )
    # Reply translated text
    line.reply_message(event.reply_token, TextMessage(text=translated_text))


def user_exists(user_id):
    return get_user_settings(user_id) != {}


def init_user_lang(user_id):
    update_user_settings(
        user_id,
        {
            user_translate_language_key: "English",
            user_audio_language_key: "Traditional Chinese",
        },
    )


def update_user_settings(user_id, settings):
    key = f"{name}.{user_id}.settings"
    current_settings = user_settings_cache.get(key) or {}
    updated_settings = {**current_settings, **settings}
    user_settings_cache.set(key, updated_settings)


def get_user_settings(user_id):
    key = f"{name}.{user_id}.settings"
    return user_settings_cache.get(key) or {}


def clean_audios(user_id):
    bucket_name = name
    minio_storage.clean_files(bucket_name, hashlib.sha256(user_id.encode()).hexdigest())


def upload_audio(user_id, audio_path):
    bucket_name = name
    minio_storage.upload_file(
        bucket_name,
        f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}",
        audio_path,
    )


def get_audio_url(user_id, audio_path):
    bucket_name = name
    return minio_storage.get_file_url(
        bucket_name,
        f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}",
    )


def get_audio_duration(audio_path):
    return tinytag_media.get_audio_duration(audio_path)


if __name__ == "__main__":
    app.run()
