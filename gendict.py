import pickle
import gzip
import sys


def gendict(txt_path: str, pickle_path: str, use_gzip=True):
    with open(txt_path, encoding="Windows-1251") as f:
        words = [line.strip() for line in f if line.strip]

    if use_gzip:
        with gzip.open(pickle_path, "wb") as f:
            pickle.dump(words, f)
    else:
        with open(pickle_path, "wb") as f:
            pickle.dump(words, f)

    print(f"[+] Saved {len(words)} words to {pickle_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python gendict.py <txt_path> <pickle_path> <use_gzip>")
        sys.exit(1)

    txt_path = sys.argv[1]
    pickle_path = sys.argv[2]
    use_gzip = sys.argv[3].lower() in ["true", "1"]

    gendict(txt_path, pickle_path, use_gzip)
