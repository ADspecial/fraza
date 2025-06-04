#!/usr/bin/env python3

import argparse
from core import generate_password
from utils import highlight_phrase


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
