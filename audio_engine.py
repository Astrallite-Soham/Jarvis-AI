"""
audio_engine.py — Jarvis Voice Processing Module
TTS : edge-tts  →  en-GB-RyanNeural  (male, British, sounds like JARVIS / TARS)
STT : SpeechRecognition + Google Web Speech API
"""

import os
import asyncio
import tempfile
import threading
import queue
import speech_recognition as sr
import pygame

# ---------------------------------------------------------------------------
# TTS Config — swap voice here if desired
# Good alternatives: "en-GB-ThomasNeural", "en-IE-ConnorNeural", "en-US-GuyNeural"
# ---------------------------------------------------------------------------
JARVIS_VOICE    = "en-GB-RyanNeural"
JARVIS_RATE     = "+8%"      # Slightly faster — confident, not rushed
JARVIS_PITCH    = "+2Hz"     # Fractionally deeper

TRIGGER_PHRASE  = "jarvis"

recognizer = sr.Recognizer()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# ---------------------------------------------------------------------------
# Internal TTS helpers
# ---------------------------------------------------------------------------

async def _tts_to_file(text: str, path: str) -> None:
    """Async: generate speech with edge-tts and save to path."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text, JARVIS_VOICE, rate=JARVIS_RATE, pitch=JARVIS_PITCH
        )
        await communicate.save(path)
    except ImportError:
        raise RuntimeError(
            "edge-tts not installed. Run: pip install edge-tts"
        )


def _play_file(path: str) -> None:
    """Blocking: play an audio file via pygame and delete afterwards."""
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(15)
        pygame.mixer.music.unload()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _speak_blocking(text: str) -> None:
    """Generate + play a single TTS segment, blocking until done."""
    text = text.strip()
    if not text:
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tmp_path = fp.name
    try:
        asyncio.run(_tts_to_file(text, tmp_path))
        _play_file(tmp_path)
    except Exception as e:
        print(f"[Jarvis TTS] Error: {e}")
        # Fallback: try gTTS if edge-tts fails
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang="en", tld="co.uk", slow=False)
            tts.save(tmp_path)
            _play_file(tmp_path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Sentence-queue TTS engine
# Speak each sentence the moment the LLM finishes generating it —
# while the LLM is still generating the next one.
# ---------------------------------------------------------------------------

class SentenceQueue:
    """
    Feed sentences via .put(text).
    They play in order, overlapping generation with playback.
    Call .finish() when done feeding.
    """

    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def put(self, text: str) -> None:
        self._q.put(text)

    def finish(self) -> None:
        """Signal end-of-stream. Does NOT wait for playback to complete."""
        self._q.put(None)

    def join(self) -> None:
        """Block until all queued audio has finished playing."""
        self._thread.join()

    def _worker(self) -> None:
        while True:
            text = self._q.get()
            if text is None:
                return
            _speak_blocking(text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def speak_text(text: str) -> None:
    """Speak the entire text synchronously (used for short one-shot replies)."""
    _speak_blocking(text)


def speak_stream(sentence_iterable) -> None:
    """
    Speak sentences as they arrive from a generator.
    Returns immediately; audio continues in background.
    Call speak_text() or speak_stream() again only after previous is done
    to avoid overlapping pygame playback.
    """
    sq = SentenceQueue()
    for sentence in sentence_iterable:
        sq.put(sentence)
    sq.finish()
    sq.join()  # Wait for all audio (called from a background thread in app_ui)


def listen_for_voice(timeout: int = 5, phrase_limit: int = 10):
    """
    Capture microphone input, return transcribed command (str) or None.
    Ignores input that doesn't contain the trigger phrase.
    """
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        print("[Jarvis] Listening...")
        try:
            audio = recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_limit
            )
        except sr.WaitTimeoutError:
            print("[Jarvis] Timeout — nothing heard.")
            return None

    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"[Jarvis] Heard: '{text}'")

        if TRIGGER_PHRASE not in text:
            print(f"[Jarvis] Trigger '{TRIGGER_PHRASE}' not found. Ignored.")
            return None

        command = text.split(TRIGGER_PHRASE, 1)[-1].strip(", ").strip()
        return command if command else None

    except sr.UnknownValueError:
        print("[Jarvis] Unintelligible audio.")
        return None
    except sr.RequestError as e:
        print(f"[Jarvis] STT error: {e}")
        return None


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Jarvis Audio Engine — voice test")
    speak_text(
        "Good evening, sir. All systems nominal. "
        "Reactor output is at one hundred percent. "
        "Shall I prepare the suit?"
    )
