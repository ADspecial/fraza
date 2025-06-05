# fraza/utils.py
import os
import sys
import json
import math
from typing import Dict

SPECIAL_CHARS = ["!", "@", "#", "$"]


def load_dict(path="data/tagged_words_full.json") -> Dict:
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
        path = os.path.join(base_path, path)
    else:
        base_path = os.path.dirname(__file__)
        path = os.path.abspath(path)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_english_layout(word: str) -> str:
    """
    Convert a Russian-layout word into the corresponding English keyboard layout.

    Maps Cyrillic characters to Latin keys based on standard keyboard layout.
    """
    ru = "ёйцукенгшщзхъфывапролджэячсмитьбю"
    en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,."

    ru_upper = ru.upper()
    en_upper = en.upper()

    layout = str.maketrans(ru + ru_upper, en + en_upper)

    return word.translate(layout)


def analyze_password(password: str) -> dict:
    from zxcvbn import zxcvbn

    result = zxcvbn(password)
    return {
        "entropy": math.log2(result["guesses"]),
        "crack_time": result["crack_times_display"][
            "offline_fast_hashing_1e10_per_second"
        ],
    }
