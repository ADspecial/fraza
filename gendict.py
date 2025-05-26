import sys
import json
import gzip
import pymorphy2
from collections import defaultdict

morph = pymorphy2.MorphAnalyzer()


def get_pos(word: str) -> str:
    parsed = morph.parse(word)[0]
    return parsed.tag.POS or "UNKN"


def gendict(txt_path: str, json_gz_path: str):
    pos_map = defaultdict(list)

    with open(txt_path, encoding="Windows-1251") as f:
        for line in f:
            word = line.strip()
            if not word:
                continue
            pos = get_pos(word)
            pos_map[pos].append(word)

    # Преобразуем defaultdict в обычный dict
    result = dict(pos_map)

    with gzip.open(json_gz_path, "wt", encoding="utf-8") as gz_out:
        json.dump(result, gz_out, ensure_ascii=False, indent=2)

    print(f"[+] Saved {sum(len(v) for v in result.values())} words to {json_gz_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python gendict.py <txt_path> <json_gz_path>")
        sys.exit(1)

    txt_path = sys.argv[1]
    json_gz_path = sys.argv[2]

    gendict(txt_path, json_gz_path)
