"""
    discord-bot-backend
"""
import logging
import os

from google.cloud import texttospeech

from backend.config import CONFIG, VOICE_PRESETS

logger = logging.getLogger("backend")

class GoogleHandler:
    """
    Static helper class to handle interfaces to Google APIs
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f'{os.getcwd()}/{CONFIG.get("general", "google_api_key")}'
    audio_config = None
    voice = None
    client = None
    voice_list = None

    @classmethod
    def initialise(cls):
        logger.info("Connecting to Google...")

        cls.client = texttospeech.TextToSpeechClient()
        settings = VOICE_PRESETS["default"]
        cls.voice = texttospeech.VoiceSelectionParams(
            language_code=settings["voice_type"][:5], name=settings["voice_type"]
        )
        cls.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=settings["pitch"],
            speaking_rate=settings["speaking_rate"]
        )
        cls.voice_list = [
            voice.name
            for voice in cls.client.list_voices(texttospeech.ListVoicesRequest()).voices
        ]
        logger.info("Initialised Google connection")

    @classmethod
    def get_speech(cls, input):
        """
        Request TTS audio binary of input phrase
        """
        resp = cls.client.synthesize_speech(
            input=input, audio_config=cls.audio_config, voice=cls.voice
        )
        cls.last_msg = resp
        return resp
