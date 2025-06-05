#!/usr/bin/env python3

import argparse
import pyperclip
import qrcode_terminal
import pyzipper
from fraza.core import generate_password, apply_difficulty
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


def save_passwords_encrypted_zip(filename, passwords_text):
    gen = generate_password()
    zip_password = gen["password"]
    with pyzipper.AESZipFile(
        filename, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(zip_password.encode())
        zf.writestr("passwords.txt", "".join(passwords_text))
    return zip_password


def main():
    parser = argparse.ArgumentParser(description="Генератор паролей на основе фраз")
    parser.add_argument(
        "-d",
        "--difficulty",
        type=str,
        default="simple",
        choices=["1", "2", "3", "simple", "standart", "complex"],
        help="Уровень сложности пароля (1:simple, 2:standart, 3:complex)",
    )
    parser.add_argument(
        "-w", "--word", type=int, help="Количество слов во фразе (max = 5)"
    )
    parser.add_argument(
        "-l", "--letter", type=int, help="Количество букв из каждого слова (max = 4)"
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
        type=int,
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

    output_lines = []
    results = []
    max_phrase_len = 0
    first_password = None
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

    for _ in range(args.passwords):
        result = generate_password(
            word_count=word_count,
            letter_limit=letter_limit,
            use_number=use_number,
            capitalized=capitalized,
            wildcard=wildcard,
            analyze=args.analyze,
        )

        phrase = result["phrase"]
        plain_phrase = " ".join(phrase)
        password = result["password"]
        if first_password is None:
            first_password = password
        highlighted_phrase, highlighted_password = highlight_phrase(
            phrase, password, args
        )

        max_phrase_len = max(max_phrase_len, len(plain_phrase))

        results.append(
            {
                "plain_phrase": plain_phrase,
                "plain_password": password,
                "highlighted_phrase": highlighted_phrase,
                "highlighted_password": highlighted_password,
                "analysis": result.get("analysis", {}),
            }
        )

    for item in results:
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
        if not args.sec:
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
