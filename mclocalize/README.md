# mclocalize

> **Warning:** This filter uses Google Translate (or other machine translators) and may not always translate everything fully or accurately. Mistakes, awkward phrasing, or untranslated text can occur. Always review and edit translations as needed.
>
> **Recommended usage:** This filter is best used as a one-time tool at the end of development to quickly generate initial translations for your project. For best results, have a fluent speaker review the output before release.

A Minecraft language file translation filter for Regolith.

## Features
- Bulk translates Minecraft `.lang` files from English to multiple target languages.
- Uses the [translators](https://github.com/UlionTse/translators) Python library (Google Translate by default).
- Supports translation caching and parallel processing for speed.
- Simple config: just specify your source file and target languages.

## Installation

You can install this filter with Regolith:
```
regolith install mclocalize
```

Or clone/download this repo and use it directly.

## Usage

### 1. Install dependencies
```
pip install translators
```

### 2. Prepare your config
Create a config JSON (or use Regolith's filter settings):
```json
{
  "source_file": "en_US.lang",
  "target_languages": ["fr", "de", "es"]
}
```
- `source_file`: The English `.lang` file to translate (relative to `RP/texts/`).
- `target_languages`: List of language codes to generate (e.g. `fr`, `de`, `es`).

### 3. Run the filter
```
python mclocalize.py '{"source_file": "en_US.lang", "target_languages": ["fr", "de", "es"]}'
```

Or, if using Regolith, add to your `config.json` filter settings:
```json
{
  "filter": "mclocalize",
  "settings": {
    "source_file": "en_US.lang",
    "target_languages": ["fr", "de", "es"]
  }
}
```

### 4. Output
- Translated `.lang` files will be created in the same folder as your source file, named by language code (e.g. `fr.lang`).

## Supported Translators
- Default: Google Translate
- Others: Bing, DeepL, Yandex, etc. (see [translators docs](https://github.com/UlionTse/translators))
- To use another, edit the `translator` argument in `mclocalize.py`.

## Notes
- The source language is always English. Only the source file name is configurable.
- Output files are stripped of trailing whitespace.

## License
MIT
