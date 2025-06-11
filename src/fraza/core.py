import json
import math
import random
import sys
from typing import Dict, List

SPECIAL_CHARS = ["!", "@", "#", "$"]


try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files


def load_dict() -> Dict:
    if getattr(sys, "frozen", False):
        import os

        base_path = sys._MEIPASS
        path = os.path.join(base_path, "data", "tagged_words_full.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        path = files("fraza.data").joinpath("tagged_words_full.json")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)


def load_dict_cached():
    if not hasattr(load_dict_cached, "_cache"):
        load_dict_cached._cache = load_dict()
    return load_dict_cached._cache


def to_english_layout(word: str) -> str:
    """
    Convert a Russian word typed in Cyrillic to its English keyboard equivalent.

    Args:
        word (str): Word in Russian Cyrillic layout.

    Returns:
        str: Word converted to English keyboard layout.
    """
    ru = "ёйцукенгшщзхъфывапролджэячсмитьбю"
    en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,."

    ru_upper = ru.upper()
    en_upper = en.upper()

    layout = str.maketrans(ru + ru_upper, en + en_upper)

    return word.translate(layout)


def analyze_password(password: str) -> dict:
    """
    Analyze password strength using zxcvbn library.

    Args:
        password (str): The password string to analyze.

    Returns:
        dict: Dictionary containing entropy (log2 of guesses) and estimated crack time.
    """
    from zxcvbn import zxcvbn

    result = zxcvbn(password)
    return {
        "entropy": math.log2(result["guesses"]),
        "crack_time": result["crack_times_display"][
            "offline_fast_hashing_1e10_per_second"
        ],
    }


def generate_phrase(dictionary: dict, word_count: int = 4) -> list:
    """
    Generate a grammatically structured phrase from a dictionary.

    Structure depends on word_count (3–5) using parts like subject, predicate, etc.

    Args:
        dictionary (dict): Word lists grouped by parts of speech.
        word_count (int): Number of words in the phrase (3–5).

    Returns:
        list: List of selected words forming a phrase.
    """

    structures = {
        3: ["subject", "predicate", "object"],
        4: ["attribute", "subject", "predicate", "object"],
        5: ["attribute", "subject", "adverbial", "predicate", "object"],
    }
    result_parts = structures.get(word_count)
    if not result_parts:
        raise ValueError("word_count должен быть от 3 до 5")

    return [random.choice(dictionary[part]) for part in result_parts]


def agree_words(words: list) -> list:
    """
    Inflect words to match the main noun's grammatical features.

    Adjusts adjectives, verbs, and secondary nouns to agree with the main noun
    by case, number, gender, and animacy when possible.

    Args:
        words (list): List of word dicts with POS tags and inflection options.

    Returns:
        list: List of inflected word strings.
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

        inflections = w.get("inflections", {})
        form = inflections.get(str(key), w["word"])
        result.append(form)

    return result


def build_password(
    words: List[str],
    letter_limit: int,
    capitalized: bool = False,
    wildcard: bool = False,
    prefix_number: str = "",
) -> str:
    """
    Build a password from a list of words with optional formatting.

    Applies letter limits, capitalization, special char separators, and a numeric prefix.

    Args:
        words (List[str]): Words to include in the password.
        letter_limit (int): Max letters per word.
        capitalized (bool): Capitalize each word if True.
        wildcard (bool): Insert special characters between words if True.
        prefix_number (str): Number to prepend to the password.

    Returns:
        str: Final formatted password.
    """
    processed = []

    for word in words:
        w = word[:letter_limit]
        if capitalized:
            w = w.capitalize()
        processed.append(to_english_layout(w))

    if wildcard:
        separators = list(SPECIAL_CHARS)
        joiners = [separators[i % len(separators)] for i in range(len(processed) - 1)]
        password = "".join(w + s for w, s in zip(processed, joiners)) + processed[-1]
    else:
        password = "".join(processed)

    if prefix_number:
        password = prefix_number + password

    return password


def apply_difficulty(
    difficulty: str = "simple",
    word_count: int = None,
    letter_limit: int = None,
    capitalized: bool = False,
    use_number: bool = False,
    wildcard: bool = False,
):
    """
    Apply preset password rules based on difficulty level.

    Returns adjusted parameters for word count, letter limit, and formatting options.

    Args:
        difficulty (str): Difficulty level ('simple', 'standart', 'complex').
        word_count (int): Optional custom word count.
        letter_limit (int): Optional custom letter limit.
        capitalized (bool): Capitalize words if True.
        use_number (bool): Prepend a number if True.
        wildcard (bool): Use special character separators if True.

    Returns:
        Tuple: (word_count, letter_limit, capitalized, use_number, wildcard)
    """
    difficulty_map = {
        "1": "simple",
        "2": "standart",
        "3": "complex",
        "simple": "simple",
        "standart": "standart",
        "complex": "complex",
    }

    level = difficulty_map.get(difficulty)
    if not level:
        raise ValueError("Некорректный уровень сложности")

    if level == "simple":
        word_count = word_count or 4
        letter_limit = letter_limit or 3
    elif level == "standart":
        word_count = 4
        letter_limit = 4
        use_number = True
        capitalized = True
    elif level == "complex":
        word_count = 5
        letter_limit = 4
        use_number = True
        capitalized = True
        wildcard = True

    return word_count, letter_limit, capitalized, use_number, wildcard


def generate_password(
    difficulty: str = None,
    word_count: int = None,
    letter_limit: int = None,
    capitalized: bool = False,
    use_number: bool = False,
    wildcard: bool = False,
    analyze: bool = False,
) -> dict:
    """
    Generate a password and phrase based on difficulty and customization options.

    Returns a dictionary with the password, phrase, and optionally analysis.
    """
    if (
        difficulty is None
        and word_count is None
        and letter_limit is None
        and not capitalized
        and not use_number
        and not wildcard
    ):
        difficulty = "simple"
    if difficulty is not None:
        word_count, letter_limit, capitalized, use_number, wildcard = apply_difficulty(
            difficulty, word_count, letter_limit, capitalized, use_number, wildcard
        )
    dictionary = load_dict_cached()
    raw_words = generate_phrase(dictionary, word_count)
    agreed_words = agree_words(raw_words)

    prefix_number = str(random.randint(10, 99)) if use_number else ""
    phrase = [w.capitalize() if capitalized else w for w in agreed_words]
    if use_number:
        phrase = [prefix_number] + phrase

    password = build_password(
        agreed_words, letter_limit, capitalized, wildcard, prefix_number
    )

    result = {
        "phrase": phrase,
        "password": password,
    }

    if analyze:
        result["analysis"] = analyze_password(password)

    return result
