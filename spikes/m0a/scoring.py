"""Deterministic, offline scoring helpers for the M0A feasibility spike."""

from __future__ import annotations

import unicodedata


def normalize_for_cer(text: str) -> str:
    """Lowercase, remove punctuation, and collapse whitespace for CER."""
    kept = []
    for char in text.casefold():
        if unicodedata.category(char).startswith("P"):
            continue
        kept.append(char)
    return " ".join("".join(kept).split())


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Return character-level Levenshtein distance divided by reference size."""
    ref = normalize_for_cer(reference)
    hyp = normalize_for_cer(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    previous = list(range(len(hyp) + 1))
    for row_index, ref_char in enumerate(ref, start=1):
        current = [row_index]
        for column_index, hyp_char in enumerate(hyp, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column_index] + 1,
                    previous[column_index - 1] + (ref_char != hyp_char),
                )
            )
        previous = current
    return previous[-1] / len(ref)


def _canonical_label(label: str) -> str:
    value = " ".join(label.strip().casefold().replace("_", "-").split())
    aliases = {
        "tanglish": "ta-latn",
        "tamil in latin script": "ta-latn",
        "tamil latin script": "ta-latn",
    }
    return aliases.get(value, value)


def label_matches(actual: str, expected: str) -> bool:
    """Compare language tags, including the spec's Tanglish aliases."""
    return _canonical_label(actual) == _canonical_label(expected)


_RANGES = {
    "ta": (0x0B80, 0x0BFF),
    "ml": (0x0D00, 0x0D7F),
    "hi": (0x0900, 0x097F),
}


def script_range_check(text: str, mode: str) -> bool:
    """Check for the required Unicode script as a pre-filter.

    Latin technical terms are permitted alongside Tamil, Malayalam, or Hindi.
    This is only a script filter; it does not determine language quality.
    """
    mode = mode.casefold()
    if mode not in {"en", "de", "ta-latn", *_RANGES}:
        raise ValueError(f"Unsupported M0A mode: {mode}")
    letters = [char for char in text if unicodedata.category(char).startswith("L")]
    if not letters:
        return False
    if mode in {"en", "de", "ta-latn"}:
        return all("LATIN" in unicodedata.name(char, "") for char in letters)
    start, end = _RANGES[mode]
    has_required = any(start <= ord(char) <= end for char in letters)
    only_required_or_latin = all(
        start <= ord(char) <= end
        or "LATIN" in unicodedata.name(char, "")
        for char in letters
    )
    return has_required and only_required_or_latin
