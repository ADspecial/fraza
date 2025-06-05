#!/usr/bin/env python3

import argparse
from fraza.core import generate_password
from fraza.utils import SPECIAL_CHARS, to_english_layout

COLORS = [
    "\033[1;31m",  # Red
    "\033[1;32m",  # Green
    "\033[1;33m",  # Yellow
    "\033[1;34m",  # Blue
    "\033[1;35m",  # Magenta
    "\033[1;36m",  # Light Blue
]
RESET = "\033[0m"
SPECIAL_CHAR_COLOR = "\033[1;37m"


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
        max_words = (args.word or 4) + 1
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


def main():
    parser = argparse.ArgumentParser(
        description="Генератор паролей на основе согласованных фраз"
    )
    parser.add_argument(
        "-d",
        "--difficulty",
        type=str,
        default="simple",
        choices=["1", "2", "3", "simple", "standart", "complex"],
        help="Уровень сложности: simple|1, standart|2, complex|3",
    )
    parser.add_argument("-w", "--word", type=int, help="Количество слов во фразе")
    parser.add_argument(
        "-l", "--letter", type=int, help="Количество букв из каждого слова"
    )
    parser.add_argument(
        "-n", "--number", action="store_true", help="Добавить числовой префикс"
    )
    parser.add_argument(
        "-c", "--capitalized", action="store_true", help="Сделать заглавные буквы"
    )
    parser.add_argument(
        "--wc",
        "--wildcard",
        action="store_true",
        dest="wildcard",
        help="Спецсимволы между словами",
    )
    parser.add_argument(
        "-p",
        "--passwords",
        type=int,
        default=1,
        help="Количество паролей для генерации",
    )
    parser.add_argument(
        "-a", "--analyze", action="store_true", help="Показать анализ сложности"
    )
    parser.add_argument("-f", "--file", help="File to save generated passwords")

    args = parser.parse_args()

    output_lines = []

    for _ in range(args.passwords):
        result = generate_password(
            difficulty=args.difficulty,
            word_count=args.word,
            letter_limit=args.letter,
            use_number=args.number,
            capitalized=args.capitalized,
            wildcard=args.wildcard,
            analyze=args.analyze,
        )

        phrase = result["phrase"]
        password = result["password"]

        highlighted_phrase, highlighted_password = highlight_phrase(
            phrase, password, args
        )

        if args.analyze and "analysis" in result:
            report = result["analysis"]
            score = report.get("score", "N/A")
            crack_time = report.get("crack_time", "N/A")
            output_line = f"{' '.join(phrase)} -> {password} | Score: {score}, Crack time: {crack_time}\n"
            print(
                f"{highlighted_phrase} -> {highlighted_password} | Score: {score}, Crack time: {crack_time}"
            )
        else:
            output_line = f"{' '.join(phrase)} -> {password}\n"
            print(f"{highlighted_phrase} -> {highlighted_password}")

        output_lines.append(output_line)

    if args.file:
        with open(args.file, "a", encoding="utf-8") as f:
            f.writelines(output_lines)


if __name__ == "__main__":
    main()
