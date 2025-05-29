import json
import sys
from pathlib import Path
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

TAGS = {"subject": [], "object": [], "predicate": [], "attribute": [], "adverbial": []}


def classify(word: str) -> str:
    parsed = morph.parse(word)[0]
    tag = parsed.tag

    if "NOUN" in tag:
        if "nomn" in tag:
            return "subject"
        elif "accs" in tag:
            return "object"
        else:
            return "subject"  # fallback
    elif "VERB" in tag or "INFN" in tag:
        return "predicate"
    elif "ADJF" in tag or "PRTF" in tag:
        return "attribute"
    elif "ADVB" in tag or "GRND" in tag:
        return "adverbial"
    else:
        return "subject"  # fallback


def main(input_file: str, output_file: str = "tagged_words.json"):
    path = Path(input_file)
    if not path.exists():
        print(f"Файл не найден: {input_file}")
        return

    with path.open(encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    for word in words:
        if len(word) > 4:
            category = classify(word)
            TAGS[category].append(word)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(TAGS, f, ensure_ascii=False, indent=2)

    print(f"Результат сохранен в {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python autotag_words.py words.txt")
    else:
        main(sys.argv[1])
