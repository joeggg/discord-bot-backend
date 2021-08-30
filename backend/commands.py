"""
    discord-bot-2 backend
"""
import logging
import traceback

from google.cloud import texttospeech

from backend.config import CONFIG
from backend.google_handler import GoogleHandler

logger = logging.getLogger("backend")

def handle_command(command, params):
    for param in API_COMMANDS[command]["params"]:
        if param not in params:
            logger.error("Missing param: %s", param)
            return
    try:
        func = API_COMMANDS[command]["func"]
        res = func(*params.values())
    except Exception as exc:
        logger.error(exc)
        logger.error(traceback.format_exc())
        res = "failure"

    return res

def say_test(text):
    # API call
    logger.info("Making Google API call")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    try:
        resp = GoogleHandler.get_speech(synthesis_input)
    except Exception as exc:
        logger.error(exc)
        logger.error(traceback.format_exc())
        return "failure"

    with open(CONFIG.get("general", "texttospeech_dir"), "wb") as file:
        file.write(resp.audio_content)
        logger.info("Google texttospeech response written")

    return "success"


API_COMMANDS = {
    "say_test": {"func": say_test, "params": ["text"]},
}
