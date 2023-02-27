"""
    discord-bot-2 backend

    API command functions

"""
import asyncio
import logging
import random
import traceback
from typing import Callable, TypedDict

from google.cloud import texttospeech

from .config import CONFIG
from .google_handler import GoogleHandler
from .reddit import meme_of_day

DICE_SET = {4, 6, 8, 10, 12, 20}


async def handle_command(command: str, params: dict) -> dict:
    """
    Checks command inputs and calls the needed function,
    handling errors and the return API response
    """
    try:
        func = API_COMMANDS[command]["func"]
        code, res = await func(*params.values())
    except Exception as exc:
        logging.exception(exc)
        return {"code": 1, "error": {"msg": str(exc), "trace": traceback.format_exc()}}

    if code == 1:
        return {"code": 1, "error": {"msg": res, "trace": ""}}

    return {"code": code, "result": res}


async def test_async():
    await asyncio.sleep(2)
    return 0, "slept"


async def say_test(text: str):
    """
    Create a TTS audio file for attaching with frontend
    """
    # API call
    logging.info("Making Google texttospeech API call")
    resp = GoogleHandler.get_speech(text)

    with open(CONFIG.get("texttospeech", "texttospeech_dir"), "wb") as file:
        file.write(resp.audio_content)
        logging.info("Google texttospeech response written")

    return 0, ""


async def set_google_preset(preset: str):
    """
    Select a TTS voice preset from saved settings
    """
    if preset not in GoogleHandler.VOICE_PRESETS:
        return 1, "Voice preset does not exist"

    settings = GoogleHandler.VOICE_PRESETS[preset]
    GoogleHandler.voice = texttospeech.VoiceSelectionParams(
        language_code=settings["voice_type"][:5], name=settings["voice_type"]
    )
    GoogleHandler.audio_config.pitch = settings["pitch"]
    GoogleHandler.audio_config.speaking_rate = settings["speaking_rate"]

    return 0, f"Voice set to {preset}"


async def change_google_voice(voice: str):
    """
    Set only TTS voice type to a specific value
    """
    logging.info("Voice requested to change to: %s", voice)

    if voice == "default":
        voice = CONFIG.get("texttospeech", "default_voice")
    elif voice not in GoogleHandler.voice_list:
        return 1, "Invalid voice type"

    GoogleHandler.voice = texttospeech.VoiceSelectionParams(language_code=voice[:5], name=voice)
    return 0, f"Voice successfully changed to {voice}"


async def change_google_pitch(pitch: str):
    """
    Set only TTS voice pitch to a specific value
    """
    logging.info("Voice pitch requested to change to: %s", pitch)

    if pitch == "default":
        pitch = CONFIG.get("texttospeech", "default_pitch")
    elif float(pitch) < -20.0 or float(pitch) > 20.0:
        return 1, "Invalid pitch"

    GoogleHandler.audio_config.pitch = float(pitch)
    return 0, f"Pitch successfully changed to {pitch}"


async def change_google_rate(rate: str):
    """
    Set only TTS speaking rate to a specific value
    """
    logging.info("Speaking rate requested to change to: %s", rate)

    if rate == "default":
        rate = CONFIG.get("texttospeech", "default_rate")
    elif float(rate) < 0.25 or float(rate) > 4.0:
        return 1, "Invalid rate"

    GoogleHandler.audio_config.speaking_rate = float(rate)
    return 0, f"Speaking rate successfully changed to {rate}"


async def dnd_dice_roll(rolls: list[str]):
    """
    Perform a set of rolls with input format ["4d12", "3d20", ...]
    [<num rolls><dice size>, ...]
    """
    results = {}
    logging.info("Performing dice roll for rolls: %s", rolls)
    for roll in rolls:
        num, dice = roll.split("d")
        if dice not in DICE_SET:
            return 1, f"Dice size d{dice} not in set"
        if int(num) < 1:
            return 1, f"Number of dice less than 1 for d{dice}"
        if int(num) > 100:
            return 1, f"{num} rolls for d{dice} is too many"

        result = [random.randint(1, int(dice)) for _ in range(int(num))]
        results[f"d{dice}"] = result

    return 0, results


class APICommand(TypedDict):
    func: Callable
    params: list[str]


API_COMMANDS: dict[str, APICommand] = {
    "memeoftheday": {"func": meme_of_day, "params": []},
    "test_async": {"func": test_async, "params": []},
    "say_test": {"func": say_test, "params": ["text"]},
    "set_google_preset": {"func": set_google_preset, "params": ["preset"]},
    "change_google_voice": {"func": change_google_voice, "params": ["voice"]},
    "change_google_pitch": {"func": change_google_pitch, "params": ["pitch"]},
    "change_google_rate": {"func": change_google_rate, "params": ["rate"]},
    "dnd_dice_roll": {"func": dnd_dice_roll, "params": ["rolls"]},
}
