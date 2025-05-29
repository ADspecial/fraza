#!/usr/bin/env python3
import argparse
import random
import json
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

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


def load_dict(path="tagged_words.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_phrase(dictionary, word_count=4):
    base = ["subject", "predicate", "object"]

    result_parts = []

    if word_count == 3:
        result_parts = base
    elif word_count == 4:
        result_parts = ["attribute"] + base
    elif word_count == 5:
        result_parts = ["attribute"] + base[:1] + ["adverbial"] + base[1:]
    else:
        raise ValueError("word_count должен быть от 3 до 5")

    words = [random.choice(dictionary[part]) for part in result_parts]
    return words


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
    if len(words) == 5:
        attribute, subject, adverbial, predicate, obj = words
    elif len(words) == 4:
        attribute, subject, predicate, obj = words
        adverbial = None
    elif len(words) == 3:
        subject, predicate, obj = words
        attribute = adverbial = None
    else:
        return words

    # Разбор subject с проверкой правильного варианта
    subj_parse = max(morph.parse(subject), key=lambda p: p.score)
    # Приводим subject к именительному, если нужно согласовывать атрибут
    subj_case = subj_parse.tag.case or "nomn"

    # 1. attribute согласуем по граммемам subject
    if attribute:
        attr_parse = max(morph.parse(attribute), key=lambda p: p.score)
        target_grammemes = {subj_parse.tag.gender, subj_parse.tag.number, subj_case}
        target_grammemes.discard(None)
        inflected = attr_parse.inflect(target_grammemes)
        if inflected:
            attribute = inflected.word

    # 2. predicate — 3 лицо, ед. число, наст. время (проверяем, что это глагол)
    pred_parse = max(morph.parse(predicate), key=lambda p: p.score)
    if pred_parse.tag.POS in {"VERB", "INFN"}:
        inflected = pred_parse.inflect({"3per", "sing", "pres"})
        if inflected:
            predicate = inflected.word

    # 3. object — склоняем в винительный, учитывая одушевлённость
    obj_parse = max(morph.parse(obj), key=lambda p: p.score)
    obj_case = "accs"
    # Уточняем одушевлённость (anim — одушевлённый)
    if "anim" in obj_parse.tag:
        inflected = obj_parse.inflect({obj_case, "anim"})
    else:
        inflected = obj_parse.inflect({obj_case})
    if inflected:
        obj = inflected.word

    result = [w for w in [attribute, subject, adverbial, predicate, obj] if w]
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
