# Replacements Filter

This repository provides a **Regolith filter** for performing string replacements in Bedrock Edition packs. It is designed to automate the process of replacing placeholder strings (such as `@namespace`, `@team`, `@proj`) with your desired values across multiple files in your project.

## Why use this filter?

This filter is especially useful for namespacing: you can define preset values (like your namespace, team, or project name) in one place and quickly change them across your entire project. This is extremely helpful when copying files from other projects, as you can instantly update all relevant identifiers to match your new project.

It works particularly well in tandem with other filters, such as the `modular_mc` Regolith filter, to streamline and modularize your Bedrock Edition development workflow.

## Installation

To install the filter, run:

```sh
regolith install replacements
```

## Usage

Add the filter to your Regolith profile in your `config.json`:

```json
{
  "regolith": {
    "profiles": {
      "default": {
        "filters": [
          {
            "filter": "replacements",
            "settings": {
              "replace": {
                "@namespace": "namespace",
                "@team": "teamname",
                "@proj": "project"
              }
            }
          }
        ]
      }
    }
  }
}
```

## Settings

The filter accepts the following settings:

- **replacements**:  
  A dictionary mapping strings to their replacements.  
  Example:
  ```json
  {
    "@namespace": "namespace",
    "@team": "teamname",
    "@proj": "project"
  }
  ```

- **extensions** (optional):  
  A list of file extensions to process.  
  Default:  
  ```json
  [".js", ".ts", ".json", ".material", ".mcfunction", ".txt", ".md"]
  ```

- **paths** (optional):  
  A list of directories to search for files to process.  
  Default:  
  ```json
  ["RP", "BP"]
  ```

## How it works

The filter scans all files in the specified `paths` with the given `extensions` and replaces every occurrence of the keys in `replacements` with their corresponding values.

## Example

Given a file with the following content:

```json
{
  "test1": "@namespace@namespace",
  "test2": "@team@namespace",
  "test3": "@proj"
}
```

With the above settings, after running the filter, it will become:

```json
{
  "test1": "namespacenamespace",
  "test2": "teamnamenamespace",
  "test3": "project"
}
```