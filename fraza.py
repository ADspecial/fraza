#!/usr/bin/env python3
import argparse
import random
import sys
import os
import json
from zxcvbn import zxcvbn

parser = argparse.ArgumentParser(description="Password generator")
parser.add_argument(
    "-d",
    "--difficulty",
    type=str,
    default="simple",
    choices=["1", "2", "3", "simple", "standart", "complex"],
    help="Уровень сложности: simple|1, standart|2, complex|3",
)
parser.add_argument("-f", "--file", help="File to save generated passwords")
parser.add_argument("-w", "--word", type=int, help="Number of words in phrase")
parser.add_argument("-l", "--letter", type=int, help="Number of letters from each word")
parser.add_argument("-n", "--number", action="store_true", help="Add a number prefix")
parser.add_argument("-c", "--capitalized", action="store_true", help="Capitalize words")
parser.add_argument(
    "--wc",
    "--wildcard",
    action="store_true",
    dest="wildcard",
    help="Add special chars between words",
)
parser.add_argument(
    "-p", "--passwords", type=int, default=1, help="Number of passwords to generate"
)
parser.add_argument(
    "-a", "--analyze", action="store_true", help="Password complexity analysis"
)

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


def load_dict(path="data/tagged_words_full.json"):
    """
    Load the JSON dictionary from the specified file path.

    Handles frozen executables by adjusting path accordingly.
    Returns dictionary loaded from JSON.
    """
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
        path = os.path.join(base_path, path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_phrase(dictionary, word_count=4):
    """
    Generate a phrase as a list of words based on the word_count.

    The phrase structure depends on word_count (3 to 5).
    Selects random words from dictionary parts accordingly.
    """
    base = ["subject", "predicate", "object"]

    if word_count == 3:
        result_parts = base
    elif word_count == 4:
        result_parts = ["attribute"] + base
    elif word_count == 5:
        result_parts = ["attribute"] + base[:1] + ["adverbial"] + base[1:]
    else:
        raise ValueError("word_count должен быть от 3 до 5")

    return [random.choice(dictionary[part]) for part in result_parts]


def to_english_layout(word):
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


def build_password(words, args, prefix_number=None):
    """
    Build the password string by processing words according to arguments.

    Applies letter limit, capitalization, layout translation, optional wildcards,
    and optional numeric prefix.
    """
    processed = []

    for word in words:
        w = word[: args.letter]
        if args.capitalized:
            w = w.capitalize()
        processed.append(to_english_layout(w))

    if args.wildcard:
        separators = ["!", "@", "#", "$", "%", "^", "&", "*"]
        joiners = [separators[i % len(separators)] for i in range(len(processed) - 1)]
        password = "".join(w + s for w, s in zip(processed, joiners)) + processed[-1]
    else:
        password = "".join(processed)

    if prefix_number:
        password = prefix_number + password

    return password


def highlight_phrase(phrase, password, args):
    """
    Highlight the phrase and password with ANSI colors.

    Colors words and corresponding letters in password for better readability.
    Also highlights special characters and digits.
    Returns a tuple of (highlighted_phrase, highlighted_password).
    """
    max_words = (args.word or 4) + 1
    max_letters = args.letter or 3

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


def save_password(password, filepath=None, phrase=None, args=None):
    """
    Print and optionally save the password with its corresponding phrase.

    Highlights the output if phrase is provided.
    Appends to file if filepath is specified.
    """
    highlighted_phrase, highlighted_password = highlight_phrase(
        phrase_view, password, args
    )
    if args.analyze:
        report = analyze_password(password)

    if phrase and args.analyze:
        print(
            f"{highlighted_phrase} -> {highlighted_password} | Score: {report['score']}, Crack time: {report['crack_time']}"
        )
    else:
        print(f"{highlighted_phrase} -> {highlighted_password}")
    if filepath:
        with open(filepath, "a", encoding="utf-8") as f:
            if args.analyze:
                f.write(
                    f"{' '.join(phrase)} -> {password} | Score: {report['score']}, Crack time: {report['crack_time']}"
                    + "\n"
                )
            else:
                f.write(f"{' '.join(phrase)} -> {password}" + "\n")


def format_phrase(words, args):
    """
    Format the phrase by capitalizing words and optionally adding a number prefix.

    Returns a tuple of (number_prefix, formatted_words_list).
    """
    formatted = [w.capitalize() if args.capitalized else w for w in words]

    if args.number:
        number = str(random.randint(10, 99))
        return number, [number] + formatted
    return "", formatted


def apply_difficulty(args):
    """
    Set argument defaults based on difficulty level.

    Adjusts word count, letter count, number prefix, capitalization, and wildcards.
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
        args.word = args.word or 4
        args.letter = args.letter or 3

    elif level == "standart":
        args.word = 4
        args.letter = 4
        args.number = True
        args.capitalized = True

    elif level == "complex":
        args.word = 5
        args.letter = 4
        args.number = True
        args.capitalized = True
        args.wildcard = True

    else:
        raise ValueError(f"Неверный уровень сложности: {args.difficulty}")


def agree_words(words):
    """
    Adjust words for grammatical agreement based on the main noun's attributes.

    Returns a list of properly inflected words where possible.
    """
    noun = next((w for w in words if w["pos"] == "NOUN"), None)
    if not noun:
        return [w["word"] for w in words]

    noun_case = noun.get("case") or "nomn"
    noun_number = noun.get("number") or "sing"
    noun_gender = noun.get("gender") or "masc"
    noun_animacy = noun.get("animacy")

    result = []
    for w in words:
        pos = w.get("pos")
        key = None

        if pos in ["ADJF", "PRTF"]:
            key = (noun_case, noun_number, noun_gender, None)

        elif pos == "NOUN" and w != noun:
            key = ("accs", noun_number, noun_gender, noun_animacy)

        elif pos in ["VERB", "INFN"]:
            # TODO: better verb agreement
            key = ("past", noun_number, noun_gender, None)

        if key and str(key) in w.get("inflections", {}):
            result.append(w["inflections"][str(key)])
        else:
            result.append(w["word"])

    return result


def analyze_password(password: str) -> dict:
    result = zxcvbn(password)
    return {
        "score": result["score"],
        "crack_time": result["crack_times_display"][
            "offline_fast_hashing_1e10_per_second"
        ],
    }


if __name__ == "__main__":
    args = parser.parse_args()
    if args.difficulty:
        apply_difficulty(args)

    dictionary = load_dict()

    for _ in range(args.passwords):
        words = generate_phrase(dictionary, args.word)
        words = agree_words(words)
        number_prefix, phrase_view = format_phrase(words, args)
        password = build_password(words, args, prefix_number=number_prefix)
        save_password(password, args.file, phrase=phrase_view, args=args)
