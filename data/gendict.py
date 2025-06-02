import json
import sys
from pathlib import Path
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

TAGS = {
    "subject": [],
    "object": [],
    "predicate": [],
    "attribute": [],
    "adverbial": [],
}


def classify(tag) -> str:
    if "NOUN" in tag:
        if "nomn" in tag:
            return "subject"
        elif "accs" in tag:
            return "object"
        else:
            return "subject"
    elif "VERB" in tag or "INFN" in tag:
        return "predicate"
    elif "ADJF" in tag or "PRTF" in tag:
        return "attribute"
    elif "ADVB" in tag or "GRND" in tag:
        return "adverbial"
    else:
        return "subject"


def analyze_word(word: str) -> dict:
    parsed = morph.parse(word)[0]
    tag = parsed.tag

    word_data = {
        "word": word,
        "normal_form": parsed.normal_form,
        "pos": tag.POS,
        "gender": tag.gender,
        "number": tag.number,
        "case": tag.case,
        "animacy": tag.animacy,
        "inflections": {},
    }

    if tag.POS in {"NOUN", "ADJF", "PRTF", "ADVB"}:
        for form in parsed.lexeme:
            form_tag = form.tag
            key = (
                form_tag.case,
                form_tag.number,
                form_tag.gender,
                form_tag.animacy,
            )
            word_data["inflections"][str(key)] = form.word

    elif tag.POS in {"VERB", "INFN"}:
        for gender in ["masc", "femn", "neut"]:
            for number in ["sing", "plur"]:
                tags = {"past", gender, number}
                inflected = parsed.inflect(tags)
                if inflected:
                    key = ("past", number, gender, None)
                    word_data["inflections"][str(key)] = inflected.word

    return word_data


def main(input_file: str, output_file: str = "tagged_words_full.json"):
    path = Path(input_file)
    if not path.exists():
        print(f"Файл не найден: {input_file}")
        return

    with path.open(encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    for word in words:
        if len(word) > 4:
            parsed = morph.parse(word)[0]
            category = classify(parsed.tag)
            TAGS[category].append(analyze_word(word))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(TAGS, f, ensure_ascii=False, indent=2)

    print(f"Результат сохранен в {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python autotag_words.py words.txt")
    else:
        main(sys.argv[1])
