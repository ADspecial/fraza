#!/usr/bin/env python3
import argparse
import sys
import random
import gzip
import pickle
from typing import List


def load_words(path: str) -> List[str]:
    try:
        with gzip.open(path, "rb") as f:
            words = pickle.load(f)
        return words
    except Exception as e:
        print(f"Error load dict: {e}")
        sys.exit(1)


# Функция для трансформации русских букв в английскую раскладку (пример)
def translate_keyboard_layout(text: str) -> str:
    layout_map = {
        "а": "f",
        "б": ",",
        "в": "d",
        "г": "u",
        "д": "l",
        "е": "t",
        "ё": "`",
        "ж": ";",
        "з": "p",
        "и": "b",
        "й": "q",
        "к": "r",
        "л": "k",
        "м": "v",
        "н": "y",
        "о": "j",
        "п": "g",
        "р": "h",
        "с": "c",
        "т": "n",
        "у": "e",
        "ф": "a",
        "х": "[",
        "ц": "w",
        "ч": "x",
        "ш": "i",
        "щ": "o",
        "ь": "m",
        "ы": "s",
        "ъ": "]",
        "э": "'",
        "ю": ".",
        "я": "z",
        "А": "F",
        "Б": "<",
        "В": "D",
        "Г": "U",
        "Д": "L",
        "Е": "T",
        "Ё": "~",
        "Ж": ":",
        "З": "P",
        "И": "B",
        "Й": "Q",
        "К": "R",
        "Л": "K",
        "М": "V",
        "Н": "Y",
        "О": "J",
        "П": "G",
        "Р": "H",
        "С": "C",
        "Т": "N",
        "У": "E",
        "Ф": "A",
        "Х": "{",
        "Ц": "W",
        "Ч": "X",
        "Ш": "I",
        "Щ": "O",
        "Ь": "M",
        "Ы": "S",
        "Ъ": "}",
        "Э": '"',
        "Ю": ">",
        "Я": "Z",
    }
    return "".join(layout_map.get(ch, ch) for ch in text)


def generate_passphrase(words: List[str], count=4) -> tuple[str, str]:
    if count > len(words):
        print(f"Error (max {len(words)})")
        sys.exit(1)
    selected = random.sample(words, count)
    phrase = " ".join(selected)
    # Берём первые 3 буквы каждого слова и переводим раскладку
    password = "".join(translate_keyboard_layout(word[:3]) for word in selected)
    return phrase, password


def main():
    parser = argparse.ArgumentParser(
        description="Password generator with passphrase (fraza)"
    )
    parser.add_argument(
        "-w",
        "--words",
        type=int,
        default=4,
        help="Number of words in the passphrase (default is 4)",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default="dict",
        help="Path to the dictionary file (pickle)",
    )

    args = parser.parse_args()
    words = load_words(args.file)
    phrase, password = generate_passphrase(words, args.words)
    print(f"Passphrase: {phrase}")
    print(f"Password: {password}")


if __name__ == "__main__":
    main()
