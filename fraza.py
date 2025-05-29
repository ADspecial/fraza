#!/usr/bin/env python3
import argparse
import random
import json

parser = argparse.ArgumentParser(description="Password generator")
parser.add_argument(
    "-d",
    "--difficulty",
    type=str,
    default="standart",
    choices=["1", "2", "3", "simple", "standart", "complex"],
    help="Уровень сложности: simple|1, standart|2, complex|3",
)
parser.add_argument("-f", "--file")
parser.add_argument("-w", "--word", type=int)
parser.add_argument("-l", "--letter", type=int)
parser.add_argument("-n", "--number", action="store_true")
parser.add_argument("-c", "--capitalized", action="store_true")
parser.add_argument("--wc", "--wildcard", action="store_true", dest="wildcard")
parser.add_argument("-p", "--passwords", type=int, default=1)


def load_dict(path="tagged_words_full.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_phrase(dictionary, word_count=4):
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
    ru = "ёйцукенгшщзхъфывапролджэячсмитьбю"
    en = "`qwertyuiop[]asdfghjkl;'zxcvbnm,."

    ru_upper = ru.upper()
    en_upper = en.upper()

    layout = str.maketrans(ru + ru_upper, en + en_upper)

    return word.translate(layout)


def build_password(words, args, prefix_number=None):
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


def save_password(password, filepath=None, phrase=None):
    if phrase:
        print(f"{' '.join(phrase)} -> {password}")
    else:
        print(f"Generated password: {password}")
    if filepath:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"{' '.join(phrase)} -> {password}" + "\n")


def format_phrase(words, args):
    formatted = [w.capitalize() if args.capitalized else w for w in words]

    if args.number:
        number = str(random.randint(10, 99))
        return number, [number] + formatted
    return "", formatted


def apply_difficulty(args):
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
        args.number = False
        args.capitalized = False
        args.wildcard = False

    elif level == "standart":
        args.word = args.word or 4
        args.letter = args.word or 3
        args.number = True
        args.capitalized = True
        args.wildcard = False

    elif level == "complex":
        args.word = args.word or 5
        args.letter = args.word or 4
        args.number = True
        args.capitalized = True
        args.wildcard = True

    else:
        raise ValueError(f"Неверный уровень сложности: {args.difficulty}")


def agree_words(words):
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
            # TODO:
            key = ("past", noun_number, noun_gender, None)

        if key and str(key) in w.get("inflections", {}):
            result.append(w["inflections"][str(key)])
        else:
            result.append(w["word"])

    return result


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
        save_password(password, args.file, phrase=phrase_view)
