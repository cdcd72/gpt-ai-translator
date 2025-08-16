from tinytag import TinyTag


class TinyTagMedia:
    def get_audio_duration(self, audio_path: str) -> float:
        audio = TinyTag.get(audio_path)
        return audio.duration if audio.duration is not None else 0.0
