"""Cryptogram generator using substitution cipher."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _generate_cipher_map(rng):
    letters = list(ALPHABET)
    shuffled = letters[:]
    for _ in range(1000):
        rng.shuffle(shuffled)
        if all(a != b for a, b in zip(letters, shuffled, strict=False)):
            break
    else:
        for i in range(len(letters)):
            if letters[i] == shuffled[i]:
                j = (i + 1) % len(letters)
                while letters[j] == shuffled[i] or letters[i] == shuffled[j]:
                    j = (j + 1) % len(letters)
                shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return dict(zip(letters, shuffled, strict=False))


def _apply_cipher(phrase, cm):
    result = []
    for ch in phrase:
        if ch.upper() in cm:
            e = cm[ch.upper()]
            result.append(e if ch.isupper() else e.lower())
        else:
            result.append(ch)
    return "".join(result)


def generate_cryptogram(phrase, difficulty="medium", seed=None):
    """Generate a cryptogram puzzle."""
    if not phrase or not any(ch.isalpha() for ch in phrase):
        raise ValueError("Phrase must contain at least one alphabetic character.")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"difficulty must be easy, medium, or hard, got '{difficulty}'")
    rng = random.Random(seed)
    cm = _generate_cipher_map(rng)
    encoded = _apply_cipher(phrase, cm)
    inv = {v: k for k, v in cm.items()}
    used = {ch.upper() for ch in phrase if ch.isalpha()}
    eu = [cm[l] for l in used if l in cm]
    hints = []
    if difficulty == "easy":
        n = min(3, len(eu))
        chosen = rng.sample(eu, n) if len(eu) >= n else eu
        hints = [{"encoded_letter": e, "decoded_letter": inv[e]} for e in chosen]
    elif difficulty == "medium" and eu:
        c = rng.choice(eu)
        hints = [{"encoded_letter": c, "decoded_letter": inv[c]}]
    freq = dict(sorted(Counter(ch.upper() for ch in encoded if ch.isalpha()).items(), key=lambda x: -x[1]))
    ul = len({ch.upper() for ch in phrase if ch.isalpha()})
    base = {"easy": 10, "medium": 40, "hard": 70}.get(difficulty, 40)
    cx = min(ul / 26, 1) * 20 + min(len(phrase) / 200, 1) * 10
    score = max(0, min(100, int(base + cx - len(hints) * 5)))
    ch_hash = hashlib.sha256(
        json.dumps({"original": phrase, "encoded": encoded, "cipher_map": cm}, sort_keys=True).encode()
    ).hexdigest()
    return {
        "original": phrase,
        "encoded": encoded,
        "cipher_map": cm,
        "hints": hints,
        "letter_frequency": freq,
        "difficulty_score": score,
        "content_hash": ch_hash,
    }
