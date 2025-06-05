import random
from .utils import (
    load_dict,
    to_english_layout,
    analyze_password,
    SPECIAL_CHARS,
)
from typing import List


def generate_phrase(dictionary: dict, word_count: int = 4) -> list:
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


def agree_words(words: list) -> list:
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


def build_password(
    words: List[str],
    letter_limit: int,
    capitalized: bool = False,
    wildcard: bool = False,
    prefix_number: str = "",
) -> str:
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


def generate_password(
    difficulty: str = "simple",
    word_count: int = None,
    letter_limit: int = None,
    capitalized: bool = False,
    use_number: bool = False,
    wildcard: bool = False,
    analyze: bool = False,
) -> dict:
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

    # Применяем настройки сложности
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

    # Загружаем словарь
    dictionary = load_dict()
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
