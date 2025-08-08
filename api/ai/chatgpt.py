import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatGPT:
    def __init__(self):
        self.model = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4.1-mini")
        self.temperature = float(os.getenv("OPENAI_COMPLETION_TEMPERATURE", "0.2"))
        self.tts_model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        self.tts_voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
        self.whisper_model = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")

    def translate(self, text, language):
        prompt = f"""Translate the provided sentence into the {language}, outputting only the translation."""
        response = client.responses.create(
            model=self.model,
            instructions=prompt,
            input=text,
            temperature=self.temperature,
        )
        return response.output_text

    def tts(self, text, audio_path):
        with client.audio.speech.with_streaming_response.create(
            model=self.tts_model, voice=self.tts_voice, input=text
        ) as response:
            response.stream_to_file(audio_path)

    def whisper(self, audio_path):
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=self.whisper_model, file=audio_file
            )
        return transcript.text
