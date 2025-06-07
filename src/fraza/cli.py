#!/usr/bin/env python3

import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import ceil
from typing import Any, List, Tuple

import pyperclip
import pyzipper
import qrcode_terminal

from fraza.core import (
    SPECIAL_CHARS,
    apply_difficulty,
    generate_password,
    to_english_layout,
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
SPECIAL_CHAR_COLOR = "\033[1;37m"


def highlight_phrase(phrase: List[str], password: str, args: Any) -> Tuple[str, str]:
    """
    Highlight phrase words and matching password letters with ANSI colors.

    Colors matching letters, digits, and special characters for clarity.
    Returns highlighted phrase and password strings.

    Args:
        phrase (List[str]): List of words in the phrase.
        password (str): The generated password string.
        args (Any): Parsed CLI arguments (expects 'difficulty' and 'no_color').

    Returns:
        Tuple[str, str]: Highlighted phrase and password.
    """
    if args.no_color:
        return " ".join(phrase), password

    difficulty_map = {
        "1": "simple",
        "2": "standart",
        "3": "complex",
        "simple": "simple",
        "standart": "standart",
        "complex": "complex",
    }
    level = difficulty_map.get(args.difficulty, "simple")

    max_words, max_letters = {
        "simple": ((args.word or 4) + 1, args.letter or 3),
        "standart": (5, 4),
        "complex": (6, 4),
    }[level]

    filtered_idx = [i for i, ch in enumerate(password) if ch not in SPECIAL_CHARS]
    pw_filtered = [password[i] for i in filtered_idx]

    def find_next_index(char, start):
        try:
            return pw_filtered.index(char, start)
        except ValueError:
            return None

    highlighted_words = []
    pw_idx = 0

    for w_idx, word in enumerate(phrase[:max_words]):
        color = COLORS[w_idx % len(COLORS)]
        eng_word = to_english_layout(word[:max_letters])
        word_chars = list(word)

        for i, c in enumerate(eng_word):
            if pw_idx >= len(pw_filtered):
                break
            found_idx = find_next_index(c, pw_idx)
            if found_idx is None:
                continue
            word_chars[i] = f"{color}{word[i]}{RESET}"
            pw_idx = found_idx + 1

        highlighted_words.append("".join(word_chars))

    highlighted_words.extend(phrase[max_words:])

    highlighted_password_chars = []
    for ch in password:
        if ch in SPECIAL_CHARS:
            highlighted_password_chars.append(f"{SPECIAL_CHAR_COLOR}{ch}{RESET}")
        elif ch.isdigit():
            highlighted_password_chars.append(f"\033[1;32m{ch}{RESET}")
        else:
            highlighted_password_chars.append(ch)

    pw_idx = 0
    for w_idx, word in enumerate(phrase[:max_words]):
        color = COLORS[w_idx % len(COLORS)]
        eng_word = to_english_layout(word[:max_letters])

        for c in eng_word:
            if pw_idx >= len(pw_filtered):
                break
            found_idx = find_next_index(c, pw_idx)
            if found_idx is None:
                continue
            pos = filtered_idx[found_idx]
            highlighted_password_chars[pos] = f"{color}{password[pos]}{RESET}"
            pw_idx = found_idx + 1

    highlighted_phrase = " ".join(highlighted_words)
    highlighted_password = "".join(highlighted_password_chars)

    return highlighted_phrase, highlighted_password


def save_passwords_encrypted_zip(filename: str, passwords_text: List[str]) -> str:
    """
    Save passwords to an AES-encrypted ZIP file with a generated password.

    Args:
        filename (str): Path to the output ZIP file.
        passwords_text (List[str]): List of password strings to save.

    Returns:
        str: The password used to encrypt the ZIP file.
    """
    gen = generate_password()
    zip_password = gen["password"]
    with pyzipper.AESZipFile(
        filename, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(zip_password.encode())
        zf.writestr("passwords.txt", "".join(passwords_text))
    return zip_password


def limited_letters(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
        raise argparse.ArgumentTypeError(
            f"Количество букв должно быть от 1 до 4, получено {value}"
        )
    return ivalue


def limited_passwords(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 10000:
        raise argparse.ArgumentTypeError(
            f"Количество паролей должно быть от 1 до 9999, получено {value}"
        )
    return ivalue


def limited_words(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 5:
        raise argparse.ArgumentTypeError(
            f"Количество слов должно быть от 1 до 5, получено {value}"
        )
    return ivalue


def generate_password_batch(
    batch_size, word_count, letter_limit, use_number, capitalized, wildcard, analyze
):
    return [
        generate_password(
            word_count=word_count,
            letter_limit=letter_limit,
            use_number=use_number,
            capitalized=capitalized,
            wildcard=wildcard,
            analyze=analyze,
        )
        for _ in range(batch_size)
    ]


def highlight_batch(items, args):
    result = []
    for item in items:
        highlighted_phrase, highlighted_password = highlight_phrase(
            item["phrase"], item["password"], args
        )
        result.append(
            {
                "plain_phrase": " ".join(item["phrase"]),
                "plain_password": item["password"],
                "highlighted_phrase": highlighted_phrase,
                "highlighted_password": highlighted_password,
                "analysis": item.get("analysis", {}),
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser(description="Генератор паролей на основе фраз")
    parser.add_argument(
        "-d",
        "--difficulty",
        type=str,
        default="simple",
        choices=["1", "2", "3", "simple", "standart", "complex"],
        help="Уровень сложности пароля (1|simple, 2|standart, 3|complex)",
    )
    parser.add_argument(
        "-w", "--word", type=limited_words, help="Количество слов во фразе (max = 5)"
    )
    parser.add_argument(
        "-l",
        "--letter",
        type=limited_letters,
        help="Количество букв из каждого слова (max = 4)",
    )
    parser.add_argument(
        "-n", "--number", action="store_true", help="Добавить числовой префикс (10-99)"
    )
    parser.add_argument(
        "-c",
        "--capitalized",
        action="store_true",
        help="Использовать заглавные буквы в начале слов",
    )
    parser.add_argument(
        "--wc",
        "--wildcard",
        action="store_true",
        dest="wildcard",
        help="Использовать спецсимволы в пароле, разграничители между словами в парольной фразе по очереди (!, @, #, $)",
    )
    parser.add_argument(
        "-p",
        "--passwords",
        type=limited_passwords,
        default=1,
        help="Количество паролей для генерации",
    )
    parser.add_argument(
        "-a", "--analyze", action="store_true", help="Показать анализ сложности"
    )
    parser.add_argument(
        "-f", "--file", help="Путь к файлу сохранения сгенерированных паролей"
    )
    parser.add_argument(
        "--cp",
        "--copy",
        action="store_true",
        dest="copy",
        help="Скопировать сгенерированные пароли в буфер обмена",
    )
    parser.add_argument(
        "--cpall",
        "--copyall",
        action="store_true",
        dest="copyall",
        help="Скопировать весь вывод в буфер обмена",
    )
    parser.add_argument(
        "--qr",
        action="store_true",
        help="Вывести QR-код сгенерированных паролей",
    )
    parser.add_argument(
        "--sec",
        help="Сохранить сгенерированные пароли в зашифрованный ZIP-файл. Пароль от файла сохраняется в буфер обмена. Нужно указать путь к файлу",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Отключить цветовую подсветку вывода",
    )

    args = parser.parse_args()

    max_console_output = 100
    max_file_output = 10000

    if args.passwords > max_file_output:
        args.passwords = max_file_output

    if args.passwords > max_console_output and not args.no_color:
        args.no_color = True

    word_count, letter_limit, capitalized, use_number, wildcard = apply_difficulty(
        args.difficulty,
        args.word,
        args.letter,
        args.capitalized,
        args.number,
        args.wildcard,
    )

    generation_settings = (
        f"# Параметры генерации:\n"
        f"Слов во фразе: {word_count}, "
        f"Букв из слова: {letter_limit}, "
        f"Цифры: {'да' if use_number else 'нет'}, "
        f"Заглавные: {'да' if capitalized else 'нет'}, "
        f"Спецсимволы: {'да' if wildcard else 'нет'}\n"
    )

    batch_size = 20
    total = args.passwords
    batches = ceil(total / batch_size)
    if args.passwords < 20:
        worker_count = 1
    elif args.passwords < 100:
        worker_count = min(2, os.cpu_count())
    else:
        worker_count = min(4, os.cpu_count())

    raw_results = []

    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(
                generate_password_batch,
                min(batch_size, total - i * batch_size),
                word_count,
                letter_limit,
                use_number,
                capitalized,
                wildcard,
                args.analyze,
            )
            for i in range(batches)
        ]
        for future in as_completed(futures):
            raw_results.extend(future.result())

    # === Параллельная подсветка ===
    results = []
    max_phrase_len = 0

    results = highlight_batch(raw_results, args)
    max_phrase_len = max(len(item["plain_phrase"]) for item in results)

    # === Вывод и сохранение ===
    output_lines = []
    for idx, item in enumerate(results):
        if idx >= max_console_output and not args.file and not args.sec:
            print(
                f"[!] Вывод ограничен {max_console_output} паролями. Остальные не выводятся в консоль."
            )
            break

        phrase = item["plain_phrase"]
        highlighted = item["highlighted_phrase"]
        pw_plain = item["plain_password"]
        pw_highlighted = item["highlighted_password"]
        analysis = item["analysis"]
        entropy = analysis.get("entropy", float("nan"))
        crack_time = analysis.get("crack_time", "N/A")

        if args.analyze and analysis:
            console_line = f"{phrase:<{max_phrase_len}} -> {pw_highlighted:<15} | Entropy bits: {entropy:5.2f}, Crack time: {crack_time}"
            file_line = f"{phrase:<{max_phrase_len}} -> {pw_plain:<15} | Entropy bits: {entropy:5.2f}, Crack time: {crack_time}"
        else:
            console_line = f"{phrase:<{max_phrase_len}} -> {pw_highlighted}"
            file_line = f"{phrase:<{max_phrase_len}} -> {pw_plain}"

        output_lines.append(file_line + "\n")
        if not args.sec and (idx < max_console_output):
            print(console_line.replace(phrase, highlighted))

    if args.sec:
        zip_filename = f"{args.sec}.zip"
        zip_password = save_passwords_encrypted_zip(zip_filename, output_lines)
        try:
            pyperclip.copy(zip_password)
            print(
                f"[+] Пароли сохранены в зашифрованный файл '{zip_filename}'. Пароль скопирован в буфер обмена."
            )
        except pyperclip.PyperclipException:
            print(
                "[!] Пароли сохранены, но не удалось скопировать пароль архива в буфер."
            )
    else:
        if args.file:
            with open(args.file, "a", encoding="utf-8") as f:
                f.write(generation_settings)
                f.writelines(output_lines)
        if args.copy:
            all_passwords_text = "\n".join(item["plain_password"] for item in results)
            try:
                pyperclip.copy(all_passwords_text)
            except pyperclip.PyperclipException as e:
                print(f"[!] Не удалось скопировать в буфер: {e}")
        if args.copyall:
            try:
                pyperclip.copy("".join(output_lines))
            except pyperclip.PyperclipException as e:
                print(f"[!] Не удалось скопировать в буфер: {e}")
        if args.qr:
            for item in results:
                print(f"QR для пароля: {item['plain_password']}")
                qrcode_terminal.draw(item["plain_password"])
                print()


if __name__ == "__main__":
    main()
