"""
brain_engine.py — Jarvis Cognitive Core  (speed-optimised)
Direct ollama client — zero LangChain overhead
Target: < 2 s to first spoken sentence on phi3
"""

import re
import ollama   # pip install ollama  (lighter than langchain_ollama)

# ── Model ─────────────────────────────────────────────────────────────────────
MODEL = "phi3"

# ── Ollama generation options — tuned for speed ───────────────────────────────
_OPTIONS = {
    "num_predict":    90,    # hard cap — JARVIS is brief, not verbose
    "num_ctx":       512,    # smaller context window → faster prefill
    "temperature":  0.72,
    "top_k":          20,    # narrower sampling → faster token selection
    "top_p":        0.85,
    "repeat_penalty": 1.1,
    "num_thread":      8,    # raise if your CPU has more cores
}

# ── System prompt — kept intentionally SHORT (<80 tokens) ─────────────────────
# Shorter prompt = faster time-to-first-token (prefill is proportional to length)
_SYSTEM = (
    "You are J.A.R.V.I.S., Tony Stark's AI. "
    "Reply in 1-2 sharp sentences. Dry British wit, mildly sarcastic. "
    "No preamble, no 'Certainly', no filler. Start your reply immediately."
)

# Sentence boundary: period/!/? followed by space or end-of-string
_SENT_RE = re.compile(r'(?<=[.!?])(?:\s|$)')

# phi3 artefact cleaner
_JUNK = re.compile(
    r'<\|[^|]+\|>|^(jarvis|assistant|ai)\s*:\s*',
    re.I | re.M,
)


# ── Pre-init — eagerly create client on import so first call has no overhead ──
_client = ollama.Client()   # connects to localhost:11434 by default


def init_if_needed() -> None:
    """No-op — client is module-level; kept for API compatibility with app_ui."""
    pass


def _clean_token(tok: str) -> str:
    """Remove phi3 special tokens only.
    NEVER call .strip() here — BPE tokens carry a leading space that IS the
    space between words. Stripping it fuses all words together."""
    return _JUNK.sub("", tok)
    # ↑ no .strip(), no .lstrip(), no .rstrip()


def _build_messages(user_input: str, dict_ctx: str) -> list[dict]:
    """
    Single user message with context folded in — avoids a separate system
    message round-trip and keeps total token count minimal.
    """
    ctx = f"\n[Dictionary: {dict_ctx}]" if dict_ctx else ""
    return [
        {"role": "system",  "content": _SYSTEM},
        {"role": "user",    "content": f"{user_input.strip()}{ctx}"},
    ]


def _format_dict(raw: dict | None) -> str:
    if not raw or not raw.get("success"):
        return ""
    word = raw.get("word", "")
    pos  = raw.get("part_of_speech", "")
    defn = raw.get("definition", "")
    ex   = raw.get("example", "")
    out  = f"{word} [{pos}]: {defn}"
    if ex:
        out += f" E.g. '{ex}'"
    return out


# ── Public streaming API ──────────────────────────────────────────────────────

def stream_sentences(user_input: str, raw_dict: dict | None = None):
    """
    Generator — yields complete sentences one-by-one as phi3 streams tokens.
    First sentence typically arrives in < 1 s on a mid-range CPU.

    Usage:
        for sentence in stream_sentences("define ephemeral"):
            speak(sentence)   # speak while next sentence generates
    """
    messages = _build_messages(user_input, _format_dict(raw_dict))
    stream   = _client.chat(model=MODEL, messages=messages,
                            stream=True, options=_OPTIONS)

    buffer = ""
    for chunk in stream:
        token = _clean_token(chunk["message"]["content"])
        if not token:
            continue
        buffer += token

        # Flush every complete sentence immediately — O(n) with regex
        parts = _SENT_RE.split(buffer)
        # parts[-1] is the incomplete trailing fragment
        for sentence in parts[:-1]:
            sentence = sentence.strip()
            if sentence:
                yield sentence
        buffer = parts[-1]   # keep the incomplete tail

    # Yield any remaining fragment (no terminal punctuation)
    tail = buffer.strip()
    if tail:
        yield tail


def generate_jarvis_reply(user_input: str, raw_dict: dict | None = None) -> str:
    """Non-streaming convenience wrapper."""
    return " ".join(stream_sentences(user_input, raw_dict))


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time
    print(f"Testing {MODEL} via direct ollama client …\n")
    t0 = time.perf_counter()
    first = True
    for s in stream_sentences("Hello Jarvis, are you online?"):
        if first:
            print(f"  First sentence in {time.perf_counter()-t0:.2f}s")
            first = False
        print(f"  ▸ {s}")
    print(f"\nTotal: {time.perf_counter()-t0:.2f}s")