# 🌐 MCLocalize

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://regolith-mc.github.io/)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**Automated language file translation for Minecraft Bedrock Edition projects.**

Bulk translate your Minecraft `.lang` files from English to multiple target languages using machine translation, making your addons accessible to players worldwide.

> ⚠️ **Important Notice**  
> This filter uses machine translation (Google Translate by default) and may not always be 100% accurate. Review and edit translations before release.
> 
> 💡 **Best Practice**  
> Use this filter as a starting point at the end of development, then have native speakers review the output.

--- ## ✨ Features

- 🌍 **Multi-Language Support**: Translate to 7+ languages including German, Spanish, French, Italian, Portuguese, and Serbian
- 🚀 **Bulk Processing**: Translates entire `.lang` files at once
- ⚡ **Smart Caching**: Avoids re-translating already processed text
- 🔄 **Parallel Processing**: Faster translation with concurrent requests
- ⚙️ **Configurable**: Simple configuration for source files and target languages
- 🎯 **Minecraft-Focused**: Designed specifically for Minecraft Bedrock Edition language files

---

## 🚀 Quick Start

### Installation
```bash
regolith install mclocalize
```

### Requirements
- **Python 3.7+**
- **Translators library**: `pip install translators`

---

## ⚙️ Usage

### 1. Install Dependencies
```bash
pip install translators
```

### 2. Configure the Filter
Add to your Regolith profile:
```json
{
  "filter": "mclocalize",
  "settings": {
    "source_file": "en_US.lang",
    "target_languages": ["fr", "de", "es", "it", "pt", "sr"]
  }
}
```

### 3. Run the Filter
```bash
regolith run
```

---

## ⚙️ Configuration

### Basic Configuration
```json
{
  "source_file": "en_US.lang",
  "target_languages": ["fr", "de", "es"]
}
```

### Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `source_file` | string | ✅ | English `.lang` file to translate (relative to `RP/texts/`) |
| `target_languages` | array | ✅ | List of language codes to generate translations for |

### Supported Language Codes

| Code | Language | Code | Language |
|------|----------|------|----------|
| `fr` | French | `de` | German |
| `es` | Spanish | `it` | Italian |
| `pt` | Portuguese | `sr` | Serbian |

---

## 📁 File Structure

The filter expects and creates files in the standard Minecraft structure:

```
RP/
└── texts/
    ├── en_US.lang          # Source file
    ├── fr_FR.lang          # Generated French
    ├── de_DE.lang          # Generated German
    ├── es_ES.lang          # Generated Spanish
    └── ...                 # Other languages
```

---

## 🛠️ Advanced Usage

### Standalone Execution
You can also run the filter directly:
```bash
python mclocalize.py '{"source_file": "en_US.lang", "target_languages": ["fr", "de"]}'
```

### Custom Translation Service
The filter uses Google Translate by default, but you can modify the script to use other services supported by the `translators` library.

---

## 📝 Example

**Input** (`en_US.lang`):
```
entity.mymod:custom_mob.name=Custom Mob
item.mymod:custom_sword.name=Custom Sword
tile.mymod:custom_block.name=Custom Block
```

**Output** (`fr_FR.lang`):
```
entity.mymod:custom_mob.name=Créature Personnalisée
item.mymod:custom_sword.name=Épée Personnalisée
tile.mymod:custom_block.name=Bloc Personnalisé
```

---

## ⚠️ Limitations & Best Practices

### Translation Quality
- Machine translation may not capture context perfectly
- Technical terms might be translated incorrectly
- Always review output with native speakers

### Performance
- Large files may take time to process
- Caching helps avoid re-translating existing content
- Parallel processing speeds up bulk translations

### Best Practices
1. **Review Translations**: Always have native speakers review the output
2. **Test in Game**: Verify translations display correctly in Minecraft
3. **Iterative Approach**: Translate in batches and review incrementally
4. **Backup Originals**: Keep your source files safe

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

*Made with ❤️ for Minecraft Bedrock creators*

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
