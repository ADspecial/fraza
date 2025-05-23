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


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    # Определяем ширину каждой колонки
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Функция для форматирования одной строки
    def format_row(row: list[str]) -> str:
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    # Печатаем заголовки
    print(format_row(headers))
    print("-+-".join("-" * width for width in col_widths))

    # Печатаем строки
    for row in rows:
        print(format_row(row))


def generate_passphrase(
    words: List[str],
    count=4,
    letters=3,
    is_capitalize: bool = False,
    is_number: bool = False,
) -> tuple[str, str]:
    if count > len(words):
        print(f"Error (max {len(words)})")
        sys.exit(1)

    selected = random.sample(words, count)
    phrase_core = " ".join(selected)

    prefix = str(random.randint(10, 99)) if is_number else ""
    phrase = f"{prefix} {phrase_core}".strip()

    password_parts = []
    if is_number:
        password_parts.append(prefix)

    for word in selected:
        part = word[:letters]
        if is_capitalize:
            part = part.capitalize()
        password_parts.append(translate_keyboard_layout(part))

    password = "".join(password_parts)

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
    parser.add_argument(
        "-c",
        "--capitalized",
        type=bool,
        default=False,
        help="Capitalize the first letters of words in a phrase (true|false)",
    )
    parser.add_argument(
        "-l",
        "--letters",
        type=int,
        default=3,
        help="Number of letters from the words of the phrase in the password (default is 3)",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=bool,
        default=False,
        help="Add a number to the beginning of a phrase (true|false)",
    )
    parser.add_argument(
        "-p",
        "--passwords",
        type=int,
        default=1,
        help="Number of generated passwords (default is 1)",
    )
    parser.add_argument(
        "-hard",
        "--hard",
        type=bool,
        default=False,
        help="Generate hard password",
    )

    args = parser.parse_args()
    if args.hard:
        args.capitalized = True
        args.letters = 3
        args.words = 4
        args.number = True

    words = load_words(args.file)
    headers = ["ID", "Passphrase", "Password"]
    data = []
    for i in range(args.passwords):
        phrase, password = generate_passphrase(
            words, args.words, args.letters, args.capitalized, args.number
        )
        data += [[i + 1, phrase, password]]
    print_table(headers, data)


if __name__ == "__main__":
    main()
