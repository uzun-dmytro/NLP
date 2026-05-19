from pathlib import Path
import json
import re


INPUT_JSON = Path("Uzun_file_2.json")
OUTPUT_TXT = Path("Uzun_file_3.txt")

WORD_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]")


def extract_lemmas_and_pos_from_conllu(conllu_text):
    pairs = []

    for line in conllu_text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        columns = line.split("\t")

        if len(columns) < 4:
            continue

        token_id = columns[0]
        form = columns[1]
        lemma = columns[2]
        upos = columns[3]

        # Пропускаємо multiword tokens і empty nodes.
        # Наприклад: 1-2 або 3.1
        if "-" in token_id or "." in token_id:
            continue

        # Прибираємо пунктуацію та символи
        if upos in {"PUNCT", "SYM"}:
            continue

        # Додатковий захист від токенів без літер
        if not WORD_RE.search(form):
            continue

        if lemma == "_":
            lemma = form

        pairs.append((lemma, upos))

    return pairs


def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Не знайдено файл: {INPUT_JSON}")

    data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))

    all_pairs = []

    chunks = data.get("chunks", [])

    print(f"Знайдено частин у JSON: {len(chunks)}")

    for chunk in chunks:
        response = chunk.get("response", {})
        conllu_result = response.get("result", "")

        pairs = extract_lemmas_and_pos_from_conllu(conllu_result)
        all_pairs.extend(pairs)

    with OUTPUT_TXT.open("w", encoding="utf-8", newline="\n") as file:
        for lemma, upos in all_pairs:
            file.write(f"{lemma} {upos}\n")

    print("Готово.")
    print(f"Файл з лемами й частинами мови збережено у: {OUTPUT_TXT}")
    print(f"Кількість рядків: {len(all_pairs)}")


if __name__ == "__main__":
    main()