import translators as ts
from pathlib import Path
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

TRANSLATION_CACHE = defaultdict(dict)

def translate_bulk(texts, target_lang, retries=3, delay=0.5):
    if not texts:
        return {}

    cache_keys = [(text, target_lang) for text in texts]
    uncached_texts = [text for text in texts if (text, target_lang) not in TRANSLATION_CACHE]

    if not uncached_texts:
        return {text: TRANSLATION_CACHE[(text, target_lang)] for text in texts}

    joined_text = "\n".join(uncached_texts)
    results = {}

    for attempt in range(retries):
        try:
            time.sleep(delay)
            translated_block = ts.translate_text(
                joined_text,
                translator='google',
                from_language='en',
                to_language=target_lang
            )
            translated_lines = translated_block.split("\n")

            if len(translated_lines) != len(uncached_texts):
                raise ValueError("Mismatch in translated lines count.")

            for original, translated in zip(uncached_texts, translated_lines):
                TRANSLATION_CACHE[(original, target_lang)] = translated
                results[original] = translated
            break
        except Exception as e:
            if attempt == retries - 1:
                print(f"❌ Bulk translation failed: {e}")
                for text in uncached_texts:
                    results[text] = text
            time.sleep(delay * (attempt + 1))

    for text in texts:
        if (text, target_lang) in TRANSLATION_CACHE:
            results[text] = TRANSLATION_CACHE[(text, target_lang)]
    return results

def translate_language_file(source_file, lang, lines):
    print(f"\n🔄 Translating to: {lang}")
    translated_lines = [None] * len(lines)
    to_translate = {}

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            translated_lines[idx] = stripped
            continue
        if '=' in stripped:
            key, value = stripped.split('=', 1)
            value = value.strip()
            if value:
                to_translate.setdefault(value, []).append((idx, key))
            else:
                translated_lines[idx] = f"{key}="
        else:
            translated_lines[idx] = stripped

    unique_texts = list(to_translate.keys())
    print(f"  📦 Bulk translating {len(unique_texts)} unique strings...")
    translations = translate_bulk(unique_texts, lang)

    for original_text, positions in to_translate.items():
        translated = translations.get(original_text, original_text)
        for idx, key in positions:
            translated_lines[idx] = f"{key}={translated}"
        print(f"    ✅ {original_text} → {translated}")

    return translated_lines

def translate_lang_file(source_file, target_langs, max_workers=4):
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    source_dir = Path(source_file).parent

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(translate_language_file, source_file, lang, lines): lang
            for lang in target_langs
        }

        for future in as_completed(futures):
            lang = futures[future]
            try:
                translated_lines = future.result()
                output_file = source_dir / f'{lang}.lang'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(translated_lines))
                print(f'✅ Created: {output_file}')
            except Exception as e:
                print(f'❌ Failed to process {lang}: {e}')

def main():
    source_file = Path(os.path.abspath(__file__)).parent / 'en_US.lang'
    target_langs = ['es', 'sr', 'fr', 'de', 'it', 'pt']
    translate_lang_file(source_file, target_langs)

if __name__ == '__main__':
    main()
