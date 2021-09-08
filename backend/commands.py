"""
    discord-bot-2 backend
"""
import logging
import random
import traceback

from google.cloud import texttospeech

from backend.config import CONFIG, VOICE_PRESETS
from backend.google_handler import GoogleHandler

logger = logging.getLogger("backend")
DICE_SET = {4, 6, 8, 10, 12, 20}

def handle_command(command, params):
    for param in API_COMMANDS[command]["params"]:
        if param not in params:
            err_msg = f"Missing param: {param}"
            logger.error(err_msg)
            return {"code": 1, "error": {"msg": err_msg, "trace": ""}}

    try:
        func = API_COMMANDS[command]["func"]
        code, res = func(*params.values())
    except Exception as exc:
        logger.error(exc)
        logger.error(traceback.format_exc())
        return {"code": 1, "error": {"msg": str(exc), "trace": traceback.format_exc()}}

    if code == 1:
        return {"code": 1, "error": {"msg": res, "trace": ""}}

    return {"code": code, "result": res}

def say_test(text):
    # API call
    logger.info("Making Google texttospeech API call")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    resp = GoogleHandler.get_speech(synthesis_input)

    with open(CONFIG.get("texttospeech", "texttospeech_dir"), "wb") as file:
        file.write(resp.audio_content)
        logger.info("Google texttospeech response written")

    return 0, ""

def set_google_preset(preset):
    if preset not in VOICE_PRESETS:
        return 1, "Voice preset does not exist"
    
    settings = VOICE_PRESETS[preset]
    GoogleHandler.voice = texttospeech.VoiceSelectionParams(
        language_code=settings["voice_type"][:5], name=settings["voice_type"]
    )
    GoogleHandler.audio_config.pitch = settings["pitch"]
    GoogleHandler.audio_config.speaking_rate = settings["speaking_rate"]

    return 0, f"Voice set to {preset}"

def change_google_voice(voice):
    logger.info("Voice requested to change to: %s", voice)
    
    if voice == "default":
        voice = CONFIG.get("texttospeech", "default_voice")
    elif voice not in GoogleHandler.voice_list:
        return 1, "Invalid voice type"

    GoogleHandler.voice = texttospeech.VoiceSelectionParams(
        language_code=voice[:5], name=voice
    )
    return 0, f"Voice successfully changed to {voice}"

def change_google_pitch(pitch):
    logger.info("Voice pitch requested to change to: %s", pitch)
    
    if pitch == "default":
        pitch = CONFIG.get("texttospeech", "default_pitch")
    elif float(pitch) < -20.0 or float(pitch) > 20.0:
        return 1, "Invalid pitch"

    GoogleHandler.audio_config.pitch = float(pitch)
    return 0, f"Pitch successfully changed to {pitch}"

def change_google_rate(rate):
    logger.info("Speaking rate requested to change to: %s", rate)
    
    if rate == "default":
        rate = CONFIG.get("texttospeech", "default_rate")
    elif float(rate) < 0.25 or float(rate) > 4.0:
        return 1, "Invalid rate"

    GoogleHandler.audio_config.speaking_rate = float(rate)
    return 0, f"Speaking rate successfully changed to {rate}"

def dnd_dice_roll(rolls):
    results = {}
    logger.info("Performing dice roll for rolls: %s", rolls)
    for roll in rolls:
        num, dice = roll.split('d')
        num = int(num)
        dice = int(dice)
        if dice not in DICE_SET:
            return 1, f"Dice size d{dice} not in set"
        if num < 1:
            return 1, f"Number of dice less than 1 for d{dice}"
        if num > 100:
            return 1, f"{num} rolls for d{dice} is too many"

        result = [random.randint(1, dice) for _ in range(num)]
        results[f"d{dice}"] = result

    return 0, results

API_COMMANDS = {
    "say_test": {"func": say_test, "params": ["text"]},
    "set_google_preset": {"func": set_google_preset, "params": ["preset"]},
    "change_google_voice": {"func": change_google_voice, "params": ["voice"]},
    "change_google_pitch": {"func": change_google_pitch, "params": ["pitch"]},
    "change_google_rate": {"func": change_google_rate, "params": ["rate"]},
    "dnd_dice_roll": {"func": dnd_dice_roll, "params": ["rolls"]},
}
