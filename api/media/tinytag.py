from tinytag import TinyTag


class TinyTagMedia:
    def get_audio_duration(self, audio_path):
        audio = TinyTag.get(audio_path)
        return audio.duration
