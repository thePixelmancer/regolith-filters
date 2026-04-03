/**
 * types.ts
 */

// ─── Docstring ────────────────────────────────────────────────────────────────

/**
 * A single @tag entry from a JSDoc docstring.
 *
 *   @group weapons
 *   This is a group of weapons.
 *
 *   → tags.group = { name: "weapons", description: "This is a group of weapons." }
 */
export interface DocstringTag {
  /** Token on the same line as the @tag, e.g. `@group weapons` → name = "weapons". */
  name: string;
  /** Body text on the lines below the @tag line. */
  description: string;
}

/**
 * Normalized view of the first JSDoc block in an asset file.
 * Produced by the `docstring()` helper in helpers.ts.
 *
 * @example
 * ```ts
 * const d = docstring(item.docstrings);
 * d.description          // leading text before any @tags
 * d.tags.group?.name     // "weapons"
 * d.tags.unique !== undefined  // existence check
 * ```
 */
export interface Docstring {
  /** Leading description text before any @tags. Empty string if absent. */
  description: string;
  /** All @tag entries keyed by tag name. First occurrence wins on duplicates. */
  tags: Record<string, DocstringTag>;
}

// ─── Raw file asset ───────────────────────────────────────────────────────────

/**
 * A plain JSON file loaded via fromGlob().
 * Has a pre-computed `.docstring` since there's no other way to
 * access the doc data on raw files.
 */
export interface RawFileAsset {
  /** Absolute path to the source file. */
  filePath: string;
  /** File name without extension, usable as a page identifier. */
  name: string;
  /** Raw parsed JSON content of the file. */
  data: Record<string, unknown>;
  /** Normalized docstring from the first JSDoc block in the file. */
  docstring: Docstring;
}

/** Any value that can appear in a COLLECTIONS entry. */
export type Asset = Record<string, unknown>;

// ─── Collection definition ────────────────────────────────────────────────────

/** Internal map of collection name → assets, passed to the renderer. */
export type CollectionMap = Map<string, Asset[]>;

// ─── Template context ─────────────────────────────────────────────────────────

/**
 * Everything available inside `{{ expr }}` and ` ```js eval ``` ` blocks.
 *
 * Named collections defined in config.ts are exposed by their exact key name.
 * e.g. a collection named "items" is available as `items` in templates.
 * `allAssets` is the union of every collection.
 */
export interface TemplateContext {
  /** The addon object — same as what's available in `js template` blocks. */
  addon: unknown;
  /** Every asset across all collections. */
  allAssets: Asset[];
  /** The asset currently being rendered. null on static pages. */
  current: Asset | null;
  /** Render an asset through its collection template. */
  render: (asset: Asset) => string;
  /** Output-relative link to an asset's doc page. */
  linkFor: (asset: Asset) => string;
  /**
   * Relative path from the current output file to a texture in rpDir.
   * Pass the texture id (e.g. `this.texture?.id`) — extension added automatically.
   * Returns empty string if texturePath is falsy.
   *
   * @example
   * `![icon]({{textureUrl(this.texture?.id)}})`
   */
  textureUrl: (texturePath: string | undefined) => string;
  /**
   * Inline a file's rendered content, or all files matching a glob pattern.
   *
   * - Specific path (relative to templateDir): renders and inlines the file.
   *   The source file is removed from the output (absorbed).
   * - Glob pattern (contains `*`, `?`, or `{}`): matches already-generated files
   *   in the output directory and concatenates their rendered content.
   *
   * The second argument controls whether inserted files are deleted from the
   * output after being inlined. Defaults to `true`.
   *
   * @example
   * `{{insert("./known_issues.md")}}`          // inlined + deleted
   * `{{insert("./blocks/*.md")}}`              // inlined + deleted
   * `{{insert("./reference.md", false)}}`      // inlined, kept as standalone file
   */
  insert: (pathOrGlob: string, absorb?: boolean) => string;
  /** Named collection arrays, keyed by exact collection name from config.ts. */
  [collectionName: string]: unknown;
}

// ─── Config ───────────────────────────────────────────────────────────────────

export interface DocGenConfig {
  outputDir: string;
  /**
   * Root template directory. Subfolder structure mirrors the output directory.
   *
   *   data/template/
   *     items.template.md     → docs/<id>.md  (one per item in "items" collection)
   *     index.md              → docs/index.md  (static, once)
   */
  templateDir: string;
}

