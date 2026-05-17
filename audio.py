"""
audio_engine.py — Jarvis Voice Processing Module
STT: SpeechRecognition + Google Web Speech API (free, online)
TTS: gTTS (default) | Kokoro-82M (commented out, local/offline)
"""

import os
import tempfile
import speech_recognition as sr

# --- TTS OPTION 1: gTTS (lightweight, requires internet) ---
from gtts import gTTS
import pygame

# --- TTS OPTION 2: Kokoro (local, offline, higher quality) ---
# Uncomment below and comment out gTTS imports above to switch
# from kokoro import KPipeline
# import soundfile as sf
# import sounddevice as sd
# import numpy as np
# KOKORO_PIPELINE = KPipeline(lang_code='a')  # 'a' = American English

TRIGGER_PHRASE = "jarvis"
recognizer = sr.Recognizer()
pygame.mixer.init()


def listen_for_voice(timeout: int = 5, phrase_limit: int = 10) -> str | None:
    """
    Captures microphone input and returns transcribed text.
    Returns None if nothing is heard or recognition fails.
    Filters out input that doesn't contain the trigger phrase.
    """
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("[Jarvis] Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            print("[Jarvis] No speech detected within timeout.")
            return None

    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"[Jarvis] Heard: '{text}'")

        if TRIGGER_PHRASE not in text:
            print(f"[Jarvis] Trigger phrase '{TRIGGER_PHRASE}' not detected. Ignoring.")
            return None

        # Strip trigger phrase and return the command
        command = text.split(TRIGGER_PHRASE, 1)[-1].strip(", ").strip()
        return command if command else None

    except sr.UnknownValueError:
        print("[Jarvis] Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"[Jarvis] STT service error: {e}")
        return None


def speak_text(text: str) -> None:
    """
    Converts text to speech and plays it through system speakers.
    Uses gTTS by default. Swap with Kokoro block for offline use.
    """
    # --- gTTS Implementation ---
    _speak_gtts(text)

    # --- Kokoro Implementation (swap in for offline/higher quality) ---
    # _speak_kokoro(text)


def _speak_gtts(text: str) -> None:
    """gTTS: online, lightweight, British accent via lang/tld params."""
    tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tmp_path = fp.name
        tts.save(tmp_path)

    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()
    os.remove(tmp_path)


def _speak_kokoro(text: str) -> None:
    """
    Kokoro-82M: fully local, high-quality TTS. No internet required.
    Requires: pip install kokoro soundfile sounddevice
    Model voices: 'af_heart', 'af_bella', 'am_adam', 'bf_emma', 'bm_george'
    """
    # samples, sample_rate = [], 24000
    # for _, _, audio in KOKORO_PIPELINE(text, voice='bm_george', speed=1.0):
    #     samples.append(audio)
    # audio_out = np.concatenate(samples)
    # sd.play(audio_out, samplerate=sample_rate)
    # sd.wait()
    pass


# --- Standalone Test ---
if __name__ == "__main__":
    print("=" * 50)
    print("Jarvis Audio Engine — Test Mode")
    print(f"Say something starting with '{TRIGGER_PHRASE.capitalize()}'...")
    print("=" * 50)

    command = listen_for_voice(timeout=8)

    if command:
        response = f"You said: {command}"
        print(f"[Jarvis] Repeating back: '{response}'")
        speak_text(response)
    else:
        print("[Jarvis] Nothing to repeat.")
        speak_text("I did not catch that, sir. Please try again.")