#!/usr/bin/env python3
import argparse
import sys
import random
import gzip
import json
from typing import Dict, List


def load_dict(path: str) -> Dict[str, List[str]]:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading dict: {e}")
        sys.exit(1)


def translate_keyboard_layout(text: str) -> str:
    layout_map = {  # сокращён для читаемости
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
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def format_row(row: list[str]) -> str:
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    print(format_row(headers))
    print("-+-".join("-" * width for width in col_widths))
    for row in rows:
        print(format_row(row))


def generate_from_template(
    dictionary: Dict[str, List[str]],
    template: List[str],
    letters: int,
    capitalize: bool,
    number: bool,
) -> tuple[str, str]:
    phrase_parts = []
    password_parts = []

    prefix = str(random.randint(10, 99)) if number else ""
    if number:
        password_parts.append(prefix)

    for pos in template:
        if pos not in dictionary or not dictionary[pos]:
            print(f"Error: part of speech '{pos}' not found or empty")
            sys.exit(1)
        word = random.choice(dictionary[pos])
        phrase_parts.append(word)

        part = word[:letters]
        if capitalize:
            part = part.capitalize()
        password_parts.append(translate_keyboard_layout(part))

    phrase = " ".join(phrase_parts)
    password = "".join(password_parts)
    return phrase, password


def main():
    parser = argparse.ArgumentParser(
        description="Password generator with template support"
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default="dict",
        required=True,
        help="Path to .json.gz dictionary",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=str,
        required=True,
        help="Template (e.g. NOUN-VERB-ADJF)",
    )
    parser.add_argument(
        "-l", "--letters", type=int, default=3, help="Letters per word in password"
    )
    parser.add_argument(
        "-n", "--number", action="store_true", help="Add number at beginning"
    )
    parser.add_argument(
        "-c", "--capitalized", action="store_true", help="Capitalize parts"
    )
    parser.add_argument(
        "-p", "--passwords", type=int, default=1, help="Number of passwords"
    )

    args = parser.parse_args()
    dictionary = load_dict(args.file)
    template = args.template.strip().upper().split("-")

    headers = ["ID", "Passphrase", "Password"]
    rows = []

    for i in range(args.passwords):
        phrase, password = generate_from_template(
            dictionary,
            template,
            args.letters,
            args.capitalized,
            args.number,
        )
        rows.append([i + 1, phrase, password])

    print_table(headers, rows)


if __name__ == "__main__":
    main()
