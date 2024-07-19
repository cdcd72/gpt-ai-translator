import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatGPT:
    def __init__(self):
        self.model = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_COMPLETION_TEMPERATURE", "0.2"))

    def whisper(self, audio_path):
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
        return transcript.text

    def translate(self, text, language):
        prompt = f"""
Help me translate this sentence to {language}, only target language, no need original language."""
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            temperature=self.temperature,
        )
        return response.choices[0].message.content
