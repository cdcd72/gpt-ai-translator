from dataclasses import dataclass
from config.base import BaseConfig
from typing import Optional
from openai import OpenAI


@dataclass
class OpenAIConfig(BaseConfig):
    api_key: str
    model: str = "gpt-5-nano"
    temperature: float = 1.0
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"
    whisper_model: str = "whisper-1"

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        return cls(
            api_key=cls.get_required("OPENAI_API_KEY"),
            model=cls.get_str("OPENAI_COMPLETION_MODEL", "gpt-5-nano"),
            temperature=cls.get_float("OPENAI_COMPLETION_TEMPERATURE", 1.0),
            tts_model=cls.get_str("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            tts_voice=cls.get_str("OPENAI_TTS_VOICE", "alloy"),
            whisper_model=cls.get_str("OPENAI_WHISPER_MODEL", "whisper-1"),
        )


class ChatGPT:
    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or OpenAIConfig.from_env()
        self.client = OpenAI(api_key=self.config.api_key)

    def translate(self, text: str, language: str) -> str:
        prompt = f"""Translate the provided sentence into the {language}, outputting only the translation."""
        response = self.client.responses.create(
            model=self.config.model,
            instructions=prompt,
            input=text,
            temperature=self.config.temperature,
        )
        return response.output_text

    def tts(self, text: str, audio_path: str) -> None:
        with self.client.audio.speech.with_streaming_response.create(
            model=self.config.tts_model, voice=self.config.tts_voice, input=text
        ) as response:
            response.stream_to_file(audio_path)

    def whisper(self, audio_path: str) -> str:
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=self.config.whisper_model, file=audio_file
            )
        return transcript.text
