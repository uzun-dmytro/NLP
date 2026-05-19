from pathlib import Path
import json
import time
import requests
from tqdm import tqdm


INPUT_FILE = Path("Uzun_file_1.txt")
OUTPUT_JSON = Path("Uzun_file_2.json")

UDPIPE_URL = "https://lindat.mff.cuni.cz/services/udpipe/api/process"
MODEL = "ukrainian-iu-ud-2.17-251125"

MAX_CHUNK_CHARS = 45_000
REQUEST_TIMEOUT = 180
MAX_RETRIES = 3


def split_text_into_chunks(text, max_chars):
    paragraphs = text.splitlines()
    chunks = []
    current = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        paragraph_len = len(paragraph)

        if paragraph_len > max_chars:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0

            for i in range(0, paragraph_len, max_chars):
                chunks.append(paragraph[i:i + max_chars])

            continue

        if current_len + paragraph_len + 1 > max_chars:
            chunks.append("\n".join(current))
            current = [paragraph]
            current_len = paragraph_len
        else:
            current.append(paragraph)
            current_len += paragraph_len + 1

    if current:
        chunks.append("\n".join(current))

    return chunks


def call_udpipe(text_chunk, chunk_index):
    payload = {
        "model": MODEL,
        "tokenizer": "",
        "tagger": "",
        "parser": "",
        "data": text_chunk,
        "output": "conllu",
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                UDPIPE_URL,
                data=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            if "result" not in data:
                raise RuntimeError(f"У відповіді UDPipe немає поля 'result': {data}")

            return data

        except Exception as error:
            last_error = error
            print(f"Помилка на частині {chunk_index}, спроба {attempt}/{MAX_RETRIES}: {error}")
            time.sleep(5 * attempt)

    raise RuntimeError(f"Не вдалося обробити частину {chunk_index}") from last_error


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Не знайдено файл: {INPUT_FILE}")

    text = INPUT_FILE.read_text(encoding="utf-8")

    print(f"Вхідний файл: {INPUT_FILE}")
    print(f"Кількість символів: {len(text)}")

    chunks = split_text_into_chunks(text, MAX_CHUNK_CHARS)

    print(f"Кількість частин: {len(chunks)}")
    print(f"Модель UDPipe: {MODEL}")

    all_responses = []

    for index, chunk in enumerate(tqdm(chunks, desc="UDPipe processing"), start=1):
        response_data = call_udpipe(chunk, index)

        all_responses.append({
            "chunk_index": index,
            "chunk_chars": len(chunk),
            "response": response_data,
        })

    output_data = {
        "source_file": str(INPUT_FILE),
        "source_chars": len(text),
        "model": MODEL,
        "chunks_count": len(chunks),
        "chunks": all_responses,
    }

    OUTPUT_JSON.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("Готово.")
    print(f"JSON збережено у: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()