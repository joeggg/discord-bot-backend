"""
    discord-bot-backend

    Google services handling

"""
import logging
import os

from google.cloud import texttospeech

from .config import CONFIG, VOICE_PRESETS

logger = logging.getLogger("backend")


class GoogleHandler:
    """
    Static helper class to handle interfaces to Google APIs
    """

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CONFIG.get("startup", "google_api_key")

    audio_config: texttospeech.AudioConfig
    voice: texttospeech.VoiceSelectionParams
    client: texttospeech.TextToSpeechClient
    voice_list: list[str] = []
    last_msg: texttospeech.SynthesizeSpeechResponse

    @classmethod
    def initialise(cls):
        logger.info("Connecting to Google...")

        cls.client = texttospeech.TextToSpeechClient()
        settings = VOICE_PRESETS["default"]
        cls.voice = texttospeech.VoiceSelectionParams(
            language_code=settings["language"][:5], name=settings["name"]
        )
        cls.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=settings["pitch"],
            speaking_rate=settings["rate"],
        )
        cls.voice_list = [
            voice.name for voice in cls.client.list_voices(texttospeech.ListVoicesRequest()).voices
        ]
        logger.info("Initialised Google connection")

    @classmethod
    def get_speech(cls, input: str):
        """
        Request TTS audio binary of input phrase
        """
        resp = cls.client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=input),
            audio_config=cls.audio_config,
            voice=cls.voice,
        )
        cls.last_msg = resp
        return resp
