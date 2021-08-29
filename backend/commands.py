"""
    discord-bot-2 backend
"""
import traceback

from google.cloud import texttospeech

from backend.config import CONFIG

def handle_command(command, params):
    for param in API_COMMANDS[command]["params"]:
        if param not in params:
            print(f"Missing param: {param}")
            return
    try:
        func = API_COMMANDS[command]["func"]
        res = func(*params.values())
    except Exception as exc:
        print(exc)
        traceback.print_exc()
        res = "failure"

    return res

def say_test(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, pitch=1, speaking_rate=0.6
    )
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB", name="en-AU-Standard-D"
    )
    # API call
    print("Making Google API call")
    try:
        resp = client.synthesize_speech(input=synthesis_input, audio_config=audio_config, voice=voice)
    except Exception as exc:
        print(exc)
        traceback.print_exc()
        return "failure"

    with open(CONFIG.get("general", "texttospeech_dir"), "wb") as file:
        file.write(resp.audio_content)
        print("Google texttospeech response written")

    return "success"


API_COMMANDS = {
    "say_test": {"func": say_test, "params": ["text"]},
}
