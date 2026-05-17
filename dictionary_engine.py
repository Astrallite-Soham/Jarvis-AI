"""
dictionary_engine.py
Data layer for the Jarvis Vocabulary Assistant.
Sources: Free Dictionary API (primary) + Merriam-Webster Dev API (etymology, stubbed if no key).
"""

import os
import requests
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FREE_DICT_BASE = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
MW_API_BASE    = "https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}"
MW_API_KEY     = os.getenv("MW_API_KEY", "")   # Set env var; empty = stub mode

REQUEST_TIMEOUT = 6  # seconds


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get(url: str) -> Optional[dict | list]:
    """GET request; returns parsed JSON or None on any failure."""
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return None          # Word not found — handled by caller
        return None
    except (requests.exceptions.RequestException, ValueError):
        return None


def _error(word: str, reason: str) -> dict:
    return {"success": False, "word": word, "error": reason}


# ---------------------------------------------------------------------------
# Free Dictionary API parser
# ---------------------------------------------------------------------------

def _parse_free_dict(data: list) -> tuple[str, str, str]:
    """
    Returns (definition, part_of_speech, example).
    Walks all meanings/definitions until it fills all three slots.
    """
    definition = part_of_speech = example = ""

    for entry in data:
        for meaning in entry.get("meanings", []):
            if not part_of_speech:
                part_of_speech = meaning.get("partOfSpeech", "")
            for defn in meaning.get("definitions", []):
                if not definition:
                    definition = defn.get("definition", "")
                if not example:
                    example = defn.get("example", "")
                if definition and example:
                    return definition, part_of_speech, example

    return definition, part_of_speech, example


# ---------------------------------------------------------------------------
# Merriam-Webster etymology (real or stubbed)
# ---------------------------------------------------------------------------

def _fetch_etymology(word: str) -> str:
    """
    Returns an etymology string.
    Falls back to a polite stub when MW_API_KEY is absent or the call fails.
    """
    if not MW_API_KEY:
        return _stub_etymology(word)

    data = _get(MW_API_BASE.format(word=word) + f"?key={MW_API_KEY}")

    if not isinstance(data, list) or not data:
        return _stub_etymology(word)

    # MW returns strings (suggestions) when the word is unrecognised
    if isinstance(data[0], str):
        return _stub_etymology(word)

    try:
        et_raw = data[0].get("et", [])
        # MW etymology is a nested list: [["text", "..."]]
        parts = [seg[1] for seg in et_raw if isinstance(seg, list) and seg[0] == "text"]
        etymology = " ".join(parts).strip()
        # Strip MW markup tags like {it}, {dx_ety}, etc.
        import re
        etymology = re.sub(r"\{[^}]+\}", "", etymology).strip()
        return etymology if etymology else _stub_etymology(word)
    except (IndexError, KeyError, TypeError):
        return _stub_etymology(word)


def _stub_etymology(word: str) -> str:
    return f"[Etymology for '{word}' unavailable — set MW_API_KEY env var for Merriam-Webster data.]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lookup(word: str) -> dict:
    """
    Primary entry point.

    Returns on success:
        {
            "success":        True,
            "word":           str,
            "part_of_speech": str,
            "definition":     str,
            "example":        str,          # may be "" if API has none
            "etymology":      str,
        }

    Returns on failure:
        { "success": False, "word": str, "error": str }
    """
    word = word.strip().lower()
    if not word:
        return _error(word, "Empty input.")

    data = _get(FREE_DICT_BASE.format(word=word))

    if data is None:
        return _error(word, f"'{word}' not found in Free Dictionary API or a network error occurred.")

    if not isinstance(data, list) or not data:
        return _error(word, "Unexpected API response format.")

    definition, part_of_speech, example = _parse_free_dict(data)

    if not definition:
        return _error(word, f"No definition extracted for '{word}'.")

    etymology = _fetch_etymology(word)

    return {
        "success":        True,
        "word":           word,
        "part_of_speech": part_of_speech or "unknown",
        "definition":     definition,
        "example":        example,
        "etymology":      etymology,
    }


def batch_lookup(words: list[str]) -> list[dict]:
    """Convenience wrapper for multiple words."""
    return [lookup(w) for w in words]


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    test_words = [
        "audacious",      # Common word — full data expected
        "serendipity",    # Good example sentence likely
        "ephemeral",
        "xyzzy",          # Nonsense — should return structured error
        "",               # Empty — should return structured error
    ]

    for w in test_words:
        result = lookup(w)
        print(json.dumps(result, indent=2))
        print("-" * 60)
