import translators as ts
from pathlib import Path
import time
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

TRANSLATION_CACHE = {}


def bulk_translate(texts, target_lang, retries=3, delay=0.5):
    """Translate a list of texts to the target language, with caching and retries."""
    if not texts:
        return {}
    uncached = [t for t in texts if (t, target_lang) not in TRANSLATION_CACHE]
    if not uncached:
        return {t: TRANSLATION_CACHE[(t, target_lang)] for t in texts}
    joined = "\n".join(uncached)
    results = {}
    for attempt in range(retries):
        try:
            if attempt > 0:
                time.sleep(delay * attempt)
            translated = ts.translate_text(
                joined,
                translator="google",
                from_language="en",
                to_language=target_lang,
            )
            lines = translated.split("\n")
            if len(lines) != len(uncached):
                raise ValueError("Mismatch in translated lines count.")
            for orig, trans in zip(uncached, lines):
                TRANSLATION_CACHE[(orig, target_lang)] = trans
                results[orig] = trans
            break
        except Exception as e:
            if attempt == retries - 1:
                print(f"Bulk translation failed: {e}")
                for t in uncached:
                    results[t] = t
    # Fill in all requested texts from cache or results
    return {
        t: TRANSLATION_CACHE.get((t, target_lang), results.get(t, t)) for t in texts
    }


def translate_lang_lines(source_file, lang, lines):
    """Translate all values in a .lang file to the target language."""
    print(f"Translating to: {lang}")
    translated_lines = [None] * len(lines)
    to_translate = {}
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            translated_lines[idx] = stripped
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            value = value.strip()
            if value:
                to_translate.setdefault(value, []).append((idx, key))
            else:
                translated_lines[idx] = f"{key}="
        else:
            translated_lines[idx] = stripped
    unique_texts = list(to_translate.keys())
    if unique_texts:
        print(f"Bulk translating {len(unique_texts)} unique strings...")
        translations = bulk_translate(unique_texts, lang)
        for original_text, positions in to_translate.items():
            translated = translations.get(original_text, original_text)
            for idx, key in positions:
                translated_lines[idx] = f"{key}={translated}"
    return translated_lines


def translate_file_to_languages(source_file, target_langs, max_workers=4):
    """Translate a .lang file to multiple target languages in parallel."""
    with open(source_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    source_dir = Path(source_file).parent
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(translate_lang_lines, source_file, lang, lines): lang
            for lang in target_langs
        }
        for future in as_completed(futures):
            lang = futures[future]
            try:
                translated_lines = future.result()
                output_file = source_dir / f"{lang}.lang"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(line.rstrip() for line in translated_lines))
                print(f"Created: {output_file}")
            except Exception as e:
                print(f"Failed to process {lang}: {e}")


def main():
    # Accept config path as first argument, else use default
    if len(sys.argv) > 1:
        config = json.loads(sys.argv[1])
    else:
        config = {}
    source_file_name = config.get("source_file", "en_US.lang")
    target_languages = config.get(
        "target_languages",
        ["fr", "de", "es"],
    )
    source_file = Path(f"RP/texts/{source_file_name}")
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    print(f"Translating {source_file} to: {', '.join(target_languages)}")
    translate_file_to_languages(source_file, target_languages)


if __name__ == "__main__":
    main()
