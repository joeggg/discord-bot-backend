"""
    discord-bot-backend
"""
import os

from google.cloud import texttospeech

from backend.config import CONFIG

class GoogleHandler:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f'{os.getcwd()}/{CONFIG.get("general", "google_api_key")}'
    client = texttospeech.TextToSpeechClient()
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, pitch=6, speaking_rate=0.6
    )
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB", name="en-AU-Standard-D"
    )
    print("Google connection set up")

    @classmethod
    def get_speech(cls, input):
        resp = cls.client.synthesize_speech(
            input=input, audio_config=cls.audio_config, voice=cls.voice
        )
        return resp
