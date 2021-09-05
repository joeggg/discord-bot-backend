"""
    discord-bot-backend
"""
import logging
import os

from google.cloud import texttospeech

from backend.config import CONFIG

logger = logging.getLogger("backend")

class GoogleHandler:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f'{os.getcwd()}/{CONFIG.get("general", "google_api_key")}'
    audio_config = None
    voice = None
    client = None
    voice_list = None

    @classmethod
    def initialise(cls):
        logger.info("Connecting to Google...")

        cls.client = texttospeech.TextToSpeechClient()
        voice = CONFIG.get("texttospeech", "default_voice")
        cls.voice = texttospeech.VoiceSelectionParams(
            language_code=voice[:5], name=voice
        )
        cls.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=CONFIG.getfloat("texttospeech", "default_pitch"),
            speaking_rate=CONFIG.getfloat("texttospeech", "default_rate")
        )
        cls.voice_list = [
            voice.name
            for voice in cls.client.list_voices(texttospeech.ListVoicesRequest()).voices
        ]
        logger.info("Initialised Google connection")

    @classmethod
    def get_speech(cls, input):
        resp = cls.client.synthesize_speech(
            input=input, audio_config=cls.audio_config, voice=cls.voice
        )
        cls.last_msg = resp
        return resp
