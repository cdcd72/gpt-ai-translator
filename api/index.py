import os
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
from api.ai.chatgpt import ChatGPT
from api.bot.line import Line
from api.config.key import ConfigKey
from api.config.language import lang_dict, reverse_lang_dict
from api.config.loader import ConfigLoader
from api.media.tinytag import TinyTagMedia
from api.storage.cache import CacheConfig, MultiTierCacheAdapter
from api.storage.minio import MinioStorage
from api.utils.audio_processor import AudioProcessor
from api.utils.user_settings_manager import UserSettingsManager

load_dotenv()

app = Flask(__name__)
ConfigLoader().apply_to(app)
app_name = app.config.get(ConfigKey.APP_NAME)
app_persistent_user_settings_enabled = app.config.get(
    ConfigKey.APP_PERSISTENT_USER_SETTINGS_ENABLED
)
app_push_translated_text_audio_enabled = app.config.get(
    ConfigKey.APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED
)

chatgpt = ChatGPT()
line = Line()
audio_processor = AudioProcessor(
    MinioStorage() if app_push_translated_text_audio_enabled else None,
    TinyTagMedia() if app_push_translated_text_audio_enabled else None,
    app_name,
)

user_translate_language_key = "translate_language"
user_audio_language_key = "audio_language"
user_settings_manager = UserSettingsManager(
    MultiTierCacheAdapter(
        CacheConfig(remote_cache_enabled=app_persistent_user_settings_enabled)
    ),
    app_name,
)


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
                    create_quick_reply_item(lang, "設定語音辨識後翻譯為 ")
                    for lang in lang_dict
                ]
            ),
        )
        line.reply_message(event.reply_token, flex_message)

    elif "設定語音辨識後翻譯為" in user_input:
        # Set audio language by user
        user_settings_manager.set_settings(
            user_id, {user_audio_language_key: lang_dict[user_input.split(" ")[1]]}
        )
        flex_message = TextMessage(
            text="請選擇對方使用語言",
            quick_reply=QuickReply(
                items=[
                    create_quick_reply_item(lang, "設定打字後翻譯為 ")
                    for lang in lang_dict
                ]
            ),
        )
        line.reply_message(event.reply_token, flex_message)

    elif "設定打字後翻譯為" in user_input:
        # Set translate language by user
        user_settings_manager.set_settings(
            user_id, {user_translate_language_key: lang_dict[user_input.split(" ")[1]]}
        )
        # Format response message
        user_settings = user_settings_manager.get_settings(user_id)
        audio_language = user_settings[user_audio_language_key]
        translate_language = user_settings[user_translate_language_key]
        response_text = f"""設定完畢！
我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line.reply_message(event.reply_token, TextMessage(text=response_text))

    elif (user_input == "/current-setting") or (user_input == "目前設定"):
        # Format response message
        user_settings = user_settings_manager.get_settings(user_id)
        audio_language = user_settings[user_audio_language_key]
        translate_language = user_settings[user_translate_language_key]
        response_text = f"""我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line.reply_message(event.reply_token, TextMessage(text=response_text))

    else:
        # Show loading animation
        line.show_loading_animation(user_id)
        # Translate text from user input
        user_settings = user_settings_manager.get_settings(user_id)
        translated_text = chatgpt.translate(
            user_input, user_settings[user_translate_language_key]
        )
        # Reply translated text
        line.reply_message(event.reply_token, TextMessage(text=translated_text))
        if app_push_translated_text_audio_enabled:
            translated_text_audio_path = os.path.join(
                app.config.get(ConfigKey.AUDIO_TEMP_PATH), f"{event.message.id}.mp3"
            )
            # Convert translated text to audio file
            chatgpt.tts(translated_text, translated_text_audio_path)
            # Operate audio file with remote storage
            audio_processor.clean_audios(user_id)
            audio_processor.upload_audio(user_id, translated_text_audio_path)
            translated_text_audio_url = audio_processor.get_audio_url(
                user_id, translated_text_audio_path
            )
            translated_text_audio_duration = (
                audio_processor.get_audio_duration(translated_text_audio_path) * 1000
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
        app.config.get(ConfigKey.AUDIO_TEMP_PATH), f"{message_id}.m4a"
    )
    line.write_audio_by_message(message_id, user_audio_path)
    whispered_text = chatgpt.whisper(user_audio_path)
    if os.path.exists(user_audio_path):
        os.remove(user_audio_path)
    # Translate text from whisper api output
    user_settings = user_settings_manager.get_settings(user_id)
    translated_text = chatgpt.translate(
        whispered_text, user_settings[user_audio_language_key]
    )
    # Reply translated text
    line.reply_message(event.reply_token, TextMessage(text=translated_text))


def user_exists(user_id):
    return user_settings_manager.get_settings(user_id) != {}


def init_user_lang(user_id):
    user_settings_manager.set_settings(
        user_id,
        {
            user_translate_language_key: "English",
            user_audio_language_key: "Traditional Chinese",
        },
    )


def create_quick_reply_item(language, prefix):
    return QuickReplyItem(action=MessageAction(label=language, text=prefix + language))


if __name__ == "__main__":
    app.run()
