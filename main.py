"""
main.py — Jarvis Master Orchestrator
CLI/headless runner. Run this directly for terminal use or integration testing.
For the full Streamlit UI, run: streamlit run app_ui.py
"""

import sys
import threading
import logging
from typing import Optional

# ── Engine imports ────────────────────────────────────────────────────────────
try:
    import audio_engine
except ImportError:
    audio_engine = None
    logging.warning("[boot] audio_engine unavailable — voice I/O disabled.")

try:
    import dictionary_engine
except ImportError:
    dictionary_engine = None
    logging.warning("[boot] dictionary_engine unavailable — definitions disabled.")

try:
    import brain_engine
except ImportError:
    brain_engine = None
    logging.warning("[boot] brain_engine unavailable — LLM responses disabled.")

# ── Config ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("jarvis")

WAKE_WORD        = "jarvis"   # Must match audio_engine.TRIGGER_PHRASE
LISTEN_TIMEOUT   = 6          # Seconds to wait for speech
PHRASE_TIME_LIMIT = 10        # Max seconds per utterance


# ── State machine ─────────────────────────────────────────────────────────────
class JarvisState:
    IDLE       = "idle"
    LISTENING  = "listening"
    PROCESSING = "processing"
    SPEAKING   = "speaking"


_state = JarvisState.IDLE


def set_state(new_state: str) -> None:
    global _state
    _state = new_state
    log.info(f"STATE → {new_state.upper()}")


# ── Core pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(query: str) -> Optional[str]:
    """
    Full Jarvis pipeline:
      query → dictionary lookup → brain synthesis → concurrent TTS + return reply
    """
    if not query.strip():
        return None

    set_state(JarvisState.PROCESSING)
    log.info(f"Query: '{query}'")

    # Step 1 — Dictionary lookup (non-blocking; None if engine absent)
    dict_payload = None
    if dictionary_engine:
        dict_payload = dictionary_engine.lookup(query.strip())
        if dict_payload and not dict_payload.get("success"):
            log.info(f"[dict] {dict_payload.get('error', 'lookup failed')}")
            dict_payload = None  # Don't pass junk to the brain

    # Step 2 — Brain synthesis
    if brain_engine:
        reply = brain_engine.generate_jarvis_reply(query.strip(), dict_payload)
    else:
        # Graceful degradation: surface raw dict data or a fallback line
        if dict_payload:
            reply = (
                f"'{dict_payload['word']}' — {dict_payload['part_of_speech']}. "
                f"{dict_payload['definition']}"
            )
        else:
            reply = f"My cognitive array is offline, sir. You asked about: '{query}'."

    log.info(f"Reply: {reply}")

    # Step 3 — Concurrent TTS + state transition
    # Speak in a daemon thread so the caller gets the reply string immediately.
    if audio_engine:
        set_state(JarvisState.SPEAKING)
        tts_thread = threading.Thread(
            target=_speak_and_idle,
            args=(reply,),
            daemon=True,
        )
        tts_thread.start()
    else:
        set_state(JarvisState.IDLE)

    return reply


def _speak_and_idle(text: str) -> None:
    """Plays TTS, then resets state. Runs in a background thread."""
    try:
        audio_engine.speak_text(text)
    except Exception as e:
        log.error(f"[tts] {e}")
    finally:
        set_state(JarvisState.IDLE)


# ── Input modes ───────────────────────────────────────────────────────────────
def voice_loop() -> None:
    """Continuous wake-word listener. Blocks until KeyboardInterrupt."""
    log.info(f"Voice loop active. Say '{WAKE_WORD.capitalize()} <word>' to query.")
    while True:
        set_state(JarvisState.LISTENING)
        try:
            command = audio_engine.listen_for_voice(
                timeout=LISTEN_TIMEOUT,
                phrase_limit=PHRASE_TIME_LIMIT,
            )
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"[stt] {e}")
            set_state(JarvisState.IDLE)
            continue

        if command:
            run_pipeline(command)
        else:
            set_state(JarvisState.IDLE)


def text_loop() -> None:
    """Interactive CLI loop. Blocks until EOF or 'exit'."""
    log.info("Text mode active. Type a word or phrase (Ctrl-C / 'exit' to quit).")
    while True:
        try:
            query = input("\n› ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if query.lower() in {"exit", "quit", "q"}:
            break
        if query:
            run_pipeline(query)

    log.info("Session ended.")


# ── Entrypoint ────────────────────────────────────────────────────────────────
def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"

    log.info("=" * 48)
    log.info("  J.A.R.V.I.S  |  Vocabulary Assistant  |  CLI")
    log.info("=" * 48)
    _log_module_status()

    if mode == "voice":
        if not audio_engine:
            log.error("audio_engine required for voice mode. Install deps and retry.")
            sys.exit(1)
        voice_loop()
    else:
        text_loop()


def _log_module_status() -> None:
    status = lambda m: "✓" if m else "✗ (degraded)"
    log.info(f"  audio_engine      {status(audio_engine)}")
    log.info(f"  dictionary_engine {status(dictionary_engine)}")
    log.info(f"  brain_engine      {status(brain_engine)}")


if __name__ == "__main__":
    main()
