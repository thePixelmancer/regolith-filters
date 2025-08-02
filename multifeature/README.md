# 🧩 MultiFeature

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://github.com/Bedrock-OSS/regolith)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

<div align="center">
  <img src="./images/banner.png" alt="MultiFeature Filter Banner" width="100%">
</div>

**A lightweight Regolith filter for simplifying Minecraft feature generation.**

## 🧩 What is this?

The **MultiFeature** filter allows you to combine multiple Minecraft feature definitions in a single file and automatically split them into individual `.json` files during the Regolith build process.

This is useful when you're working with many related features and want to keep your logic grouped together in a single place — without using more complex or opinionated tools.

> 📦 Install it via:
>
> ```
> regolith install multifeature
> ```

---

## 🆚 Why not use `MiniFeature`?

There’s a more advanced filter called [`MiniFeature`](https://github.com/BigChungus21220/minifeature-regolith-filter) which provides powerful capabilities like:

- Inline features
- YAML support
- Templating
- Conditional logic
- Outputting multiple file types

However, **this filter is purposefully simpler**.

### When to use `MultiFeature`:

- You only want to combine multiple features into a single file.
- You don’t need YAML, templating, or logic.
- You already use other filters for those tasks.
- You want to avoid conflicts with more opinionated filters like `MiniFeature`.

---

## 💡 How it works

This filter scans the `BP/multifeatures/` folder and finds all files ending in `.multifeature.json`. Each of these files is expected to be a **list of feature objects** (rather than a single feature). The filter will:

1. Parse each feature inside the list.
2. Update its identifier and `places_feature` fields using a custom subfolder prefix (if configured).
3. Export it to `BP/features/` or `BP/feature_rules/`, depending on the feature type.
4. Automatically create the correct folder structure.

### Example Input (`my_features.multifeature.json`)

```json
[
  {
    "format_version": "1.18.0",
    "minecraft:feature_rules": {
      "description": {
        "identifier": "mymod:trees/oak_forest",
        "places_feature": "mymod:trees/oak_tree"
      },
      ...
    }
  },
  ...
]
```

## 📦 Integration

This filter is best used alongside others for:

- String replacements
- Json templating
- YAML-to-JSON conversion

Check out my other filters for these capabilities — this one is kept **minimal by design**, so you can mix and match as needed.

---

## 🤝 Contribute

Feel free to fork, submit issues, or send pull requests. You can also contact me on Discord if you have questions or feature requests. I’ll be happy to review contributions quickly.

---

## ✅ Summary

| Feature                             | Supported                    |
| ----------------------------------- | ---------------------------- |
| Multi-feature files                 | ✅ Yes                       |
| Subfolder path injection            | ✅ Yes                       |
| Identifier rewriting                | ✅ Yes                       |
| YAML support                        | ❌ No (use dedicated filter) |
| Templating                          | ❌ No (use dedicated filter) |
| "namespace:" and string replacments | ❌ No (use dedicated filter) |

---

## 🚫 Inline Features Not Supported (and Why)

This filter **does not support inline/nested features**. This is intentional:

- Inline features can hurt readability, especially for large or complex projects.
- Minecraft features can only place other features in a strictly 1-to-1, linear fashion—nesting does not create a true hierarchy.
- For aggregate features (where multiple features are spawned), it is strongly recommended to create separate files for each feature. This keeps your project organized and easy to maintain.

## 📝 YAML & Modularity Strongly Recommended

I highly recommend using YAML for your feature definitions and project files. YAML is more readable, supports multiline strings, and allows you to use visual breaks (like `---`) to separate entries or sections. For example, you can use `---` to divide files or for multiline strings, making your files much easier to read and edit.

To work with YAML or multiline strings in JSON, use my [Jsonify filter](https://github.com/BigChungus21220/jsonify-regolith-filter) (the bread and butter of my workflow). Jsonify lets you:

- Write your entire project in YAML, not just features.
- Use multiline strings in JSON directly.
- Choose your own listing syntax and file organization.

**All my filters are modular:** only use what you need, and combine them as you see fit for your workflow.

If you’re looking for a full-featured system: use `MiniFeature`.

If you just want a clean, focused solution for breaking up feature files — this is the tool for you.

Made with ❤️ for Minecraft Bedrock creators.

---

## 🛠️ VS Code: Schema Support for `.multifeature.json`

**Good news!** Schema support is now automatically installed when you run this filter.

The filter will automatically configure VS Code to provide validation and autocompletion for your `.multifeature.json` files by adding the appropriate schema association to your VS Code settings.

If you need to manually configure it (or prefer to do it yourself), you can:

1. Open your VS Code settings (`Ctrl+,` or `Cmd+,`).
2. Search for `json.schemas` and click `Edit in settings.json`.
3. Add an entry like this:

   ```json
   "json.schemas": [
     {
       "fileMatch": ["*.multifeature.json"],
       "url": "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/multifeature/data/multifeature.schema.json"
     }
   ]
   ```

This will enable validation and helpful autocompletion for all `.multifeature.json` files in your workspace.
