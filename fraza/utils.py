# fraza/utils.py
import os
import sys
import json
from typing import Dict

COLORS = [
    "\033[1;31m",  # Red
    "\033[1;32m",  # Green
    "\033[1;33m",  # Yellow
    "\033[1;34m",  # Blue
    "\033[1;35m",  # Magenta
    "\033[1;36m",  # Light Blue
]
RESET = "\033[0m"
SPECIAL_CHARS = set("!@#$%^&*")
SPECIAL_CHAR_COLOR = "\033[1;37m"


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
        "score": result["score"],
        "crack_time": result["crack_times_display"][
            "offline_fast_hashing_1e10_per_second"
        ],
    }


def highlight_phrase(phrase, password, args):
    """
    Highlight the phrase and password with ANSI colors.

    Colors words and corresponding letters in password for better readability.
    Also highlights special characters and digits.
    Returns a tuple of (highlighted_phrase, highlighted_password).
    """
    difficulty_map = {
        "1": "simple",
        "2": "standart",
        "3": "complex",
        "simple": "simple",
        "standart": "standart",
        "complex": "complex",
    }
    level = difficulty_map.get(args.difficulty)
    if level == "simple":
        max_words = args.word or 4
        max_letters = args.letter or 3
    elif level == "standart":
        max_words = 5
        max_letters = 4
    elif level == "complex":
        max_words = 6
        max_letters = 4

    filtered_pos_to_password_idx = [
        i for i, ch in enumerate(password) if ch not in SPECIAL_CHARS
    ]
    pw_filtered = [password[i] for i in filtered_pos_to_password_idx]

    highlighted_words = []
    pw_idx = 0

    for w_idx, word in enumerate(phrase[:max_words]):
        color = COLORS[w_idx % len(COLORS)]
        eng_word = to_english_layout(word[:max_letters])
        word_chars = list(word)

        for i in range(min(max_letters, len(word))):
            if pw_idx >= len(pw_filtered):
                break

            try:
                found_idx = pw_filtered.index(eng_word[i], pw_idx)
            except ValueError:
                found_idx = None

            if found_idx is not None:
                word_chars[i] = f"{color}{word[i]}{RESET}"
                pw_idx = found_idx + 1

        highlighted_words.append("".join(word_chars))

    if len(phrase) > max_words:
        highlighted_words.extend(phrase[max_words:])

    highlighted_password_chars = list(password)
    for i, ch in enumerate(password):
        if ch in SPECIAL_CHARS:
            highlighted_password_chars[i] = f"{SPECIAL_CHAR_COLOR}{ch}{RESET}"
        elif ch.isdigit():
            highlighted_password_chars[i] = f"\033[1;32m{ch}{RESET}"

    pw_idx = 0
    for w_idx, word in enumerate(phrase[:max_words]):
        color = COLORS[w_idx % len(COLORS)]
        eng_word = to_english_layout(word[:max_letters])
        for i in range(min(max_letters, len(word))):
            if pw_idx >= len(pw_filtered):
                break
            try:
                found_idx = pw_filtered.index(eng_word[i], pw_idx)
            except ValueError:
                found_idx = None

            if found_idx is not None:
                pos = filtered_pos_to_password_idx[found_idx]
                highlighted_password_chars[pos] = f"{color}{password[pos]}{RESET}"
                pw_idx = found_idx + 1

    highlighted_password = "".join(highlighted_password_chars)
    highlighted_phrase = " ".join(highlighted_words)

    return highlighted_phrase, highlighted_password
