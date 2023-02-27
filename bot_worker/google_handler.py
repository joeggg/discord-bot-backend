"""
    discord-bot-backend

    Google services handling

"""
import json
import logging
from typing import TypedDict

from google.cloud import texttospeech

from .config import CONFIG


class VoicePreset(TypedDict):
    language: str
    name: str
    pitch: float
    rate: float
    gender: str


def load_voice_presets() -> dict[str, VoicePreset]:
    with open(f'{CONFIG.get("startup", "data_path")}/voice_presets.json', "r") as file:
        preset_data = json.load(file)
    return preset_data


class GoogleHandler:
    """
    Static helper class to handle interfaces to Google APIs
    """

    VOICE_PRESETS: dict[str, VoicePreset] = load_voice_presets()

    audio_config: texttospeech.AudioConfig
    voice: texttospeech.VoiceSelectionParams
    client: texttospeech.TextToSpeechClient
    voice_list: list[str] = []

    @classmethod
    def initialise(cls) -> None:
        logging.info("Connecting to Google...")
        cls.client = texttospeech.TextToSpeechClient()

        settings = cls.VOICE_PRESETS["default"]
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
        logging.info("Initialised Google connection")

    @classmethod
    def get_speech(cls, input: str) -> texttospeech.SynthesizeSpeechResponse:
        """
        Request TTS audio binary of input phrase
        """
        resp = cls.client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=input),
            audio_config=cls.audio_config,
            voice=cls.voice,
        )
        return resp
