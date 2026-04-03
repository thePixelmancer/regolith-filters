/**
 * renderer.ts
 *
 * Two-phase documentation renderer.
 *
 * Phase 1 — Template expansion:
 *   Each *.template.md generates one output file per asset.
 *   Files are written to disk immediately so Phase 2 can glob them.
 *
 * Phase 2 — Static rendering:
 *   Plain .md files are rendered and written. Files absorbed by insert() are removed.
 *
 * ── Inline: `{{expression}}`
 *   Any JS expression. `this` / `current` is the asset being rendered (null on static pages).
 *   If the expression is the only thing on the line and evaluates to empty/false,
 *   the entire line is dropped (no blank line left behind).
 *
 * ── Block: ` ```js eval ``` `
 *   Same scope as inline. Multi-line. Use for lists, tables, and multi-section output.
 *   Returning a plain object instead of a string merges it into the page context,
 *   making its properties available to all subsequent blocks and {{ }} tokens —
 *   use this to define page-scoped helpers without a separate directive.
 *
 * ── Collection: ` ```js template ``` `  (*.template.md only)
 *   Declares what assets this template generates pages for.
 *   `addon` is in scope. Must return an array.
 *
 * ── Insert: `insert(pathOrGlob)`
 *   Available as a function in all ` ```js eval ``` ` blocks and {{ }} tokens.
 *   - Specific path (relative to templateDir): renders the file inline and removes it from output.
 *   - Glob pattern (contains * ? {}): matches already-generated files in outputDir and
 *     concatenates their content. Useful for inlining all generated pages for a collection.
 *
 *   Examples:
 *     `{{insert("./known_issues.md")}}`         ← specific static file
 *     `{{insert("./blocks/*.md")}}`             ← all generated block pages
 */

import { join, dirname, relative, resolve } from "@std/path";
import { globToRegExp } from "@std/path";
import { buildContext } from "./collector.ts";
import {
  assetId,
  evalTemplateBlock,
  renderTemplate,
  makeTextureUrl,
} from "./engine.ts";
import type { Asset, DocGenConfig, TemplateContext } from "./types.ts";

// ─── File helpers ─────────────────────────────────────────────────────────────

function exists(p: string): boolean {
  try { Deno.statSync(p); return true; } catch { return false; }
}

function write(filePath: string, content: string): void {
  Deno.mkdirSync(dirname(filePath), { recursive: true });
  Deno.writeTextFileSync(filePath, content.replace(/\n{3,}/g, "\n\n").trimEnd() + "\n");
  console.log(`✍️  ${filePath}`);
}

function readFile(p: string): string | null {
  try { return Deno.readTextFileSync(p); } catch { return null; }
}

// ─── Template discovery ───────────────────────────────────────────────────────

interface TemplateFile {
  absPath: string;
  relPath: string;
  isGenerated: boolean;
  subDir: string;
}

function walkTemplates(dir: string, templateDir: string): TemplateFile[] {
  const results: TemplateFile[] = [];
  if (!exists(dir)) return results;
  for (const entry of Deno.readDirSync(dir)) {
    const absPath = join(dir, entry.name);
    if (entry.isDirectory) {
      results.push(...walkTemplates(absPath, templateDir));
    } else if (entry.isFile && entry.name.endsWith(".md")) {
      const relPath = relative(templateDir, absPath);
      const isGenerated = entry.name.endsWith(".template.md");
      results.push({ absPath, relPath, isGenerated, subDir: dirname(relPath) });
    }
  }
  return results;
}

/** Recursively removes all empty directories under (and including) `dir`. */
function pruneEmptyDirs(dir: string): void {
  try {
    for (const entry of Deno.readDirSync(dir)) {
      if (entry.isDirectory) pruneEmptyDirs(join(dir, entry.name));
    }
    // Re-check: remove this dir if it's now empty (and not the root outputDir)
    const entries = [...Deno.readDirSync(dir)];
    if (entries.length === 0) Deno.removeSync(dir);
  } catch { /* skip unreadable or already-removed dirs */ }
}

function copyDir(src: string, dest: string): void {
  Deno.mkdirSync(dest, { recursive: true });
  for (const entry of Deno.readDirSync(src)) {
    const s = join(src, entry.name), d = join(dest, entry.name);
    entry.isDirectory ? copyDir(s, d) : Deno.copyFileSync(s, d);
  }
}

// ─── Path helpers ─────────────────────────────────────────────────────────────

/** Normalise a templateDir-relative path to forward slashes with no leading ./  */
function normTplPath(p: string): string {
  return p.replace(/\\/g, "/").replace(/^\.\//, "");
}

function isGlob(p: string): boolean {
  return p.includes("*") || p.includes("?") || p.includes("{");
}

/**
 * Rewrites relative markdown links/images and HTML src/href attributes in `content`
 * so they resolve correctly when the content moves from `fromFile` to `toFile`.
 */
function rewritePaths(content: string, fromFile: string, toFile: string): string {
  if (fromFile === toFile) return content;
  const fromDir = dirname(fromFile);
  const toDir = dirname(toFile);
  const rewrite = (path: string): string => {
    if (!path || /^(https?:|#|\/|data:)/.test(path)) return path;
    const abs = resolve(fromDir, path);
    const rel = relative(toDir, abs).replace(/\\/g, "/");
    return rel.startsWith(".") ? rel : `./${rel}`;
  };
  return content
    .replace(/(!?\[[^\]]*\])\(([^)\s]+)\)/g, (_m, label, path) => `${label}(${rewrite(path)})`)
    .replace(/(src|href)="([^"]+)"/g, (_m, attr, path) => `${attr}="${rewrite(path)}"`);
}

/** Synchronously walk a directory, returning files whose relative path matches the glob. */
function syncGlob(pattern: string, baseDir: string): string[] {
  const regex = globToRegExp(pattern.replace(/^\.\//, ""), { extended: true, globstar: true });
  const results: string[] = [];
  function walk(dir: string, rel: string) {
    try {
      for (const entry of Deno.readDirSync(dir)) {
        const entryRel = rel ? `${rel}/${entry.name}` : entry.name;
        if (entry.isDirectory) walk(join(dir, entry.name), entryRel);
        else if (entry.isFile && regex.test(entryRel)) results.push(join(dir, entry.name));
      }
    } catch { /* skip unreadable dirs */ }
  }
  walk(baseDir, "");
  return results.sort();
}

// ─── Main entry point ─────────────────────────────────────────────────────────

export function render(addon: unknown, config: DocGenConfig): void {
  console.log(`\n📄 Rendering → ${config.outputDir}/\n`);

  // Wipe outputDir, then copy the entire templateDir as the base output structure
  if (exists(config.outputDir)) Deno.removeSync(config.outputDir, { recursive: true });
  copyDir(config.templateDir, config.outputDir);

  const templates = walkTemplates(config.templateDir, config.templateDir);

  // ── Collect template blocks → build collection map ────────────────────────
  const rawCollections: Record<string, Asset[]> = {};
  const templateMap = new Map<string, { src: string; subDir: string }>();

  for (const t of templates) {
    if (!t.isGenerated) continue;
    const raw = readFile(t.absPath);
    if (!raw) continue;
    const [name, assets, src] = evalTemplateBlock(raw, addon);
    if (!name) {
      console.error(`  ⚠️  ${t.relPath}: js template tag is missing a collection name — use \`\`\`js template <name>`);
      continue;
    }
    rawCollections[name] = assets;
    templateMap.set(name, { src, subDir: t.subDir });
  }

  const { ctx, collections } = buildContext(rawCollections);

  console.log("\n🔍 Collections:");
  for (const [name, assets] of collections) {
    console.log(`   ${name}: ${assets.length}`);
  }

  const attachmentsDir = join(config.outputDir, "attachments");
  const rpDir = "RP";

  /** Returns the absolute output path for an asset, or undefined if not in any collection. */
  const absPathFor = (asset: Asset): string | undefined => {
    for (const [stem, assets] of collections) {
      if (!templateMap.has(stem)) continue;
      if (assets.includes(asset)) {
        const { subDir } = templateMap.get(stem)!;
        const name = `${assetId(asset)}.md`;
        return subDir === "." ? join(config.outputDir, name) : join(config.outputDir, subDir, name);
      }
    }
    return undefined;
  };

  // absorbedOutPaths: absolute output paths absorbed by insert() — skipped when writing, deleted at end
  const absorbedOutPaths = new Set<string>();

  const makeFileCtx = (
    fromFile: string,
  ): Pick<TemplateContext, "textureUrl" | "render" | "insert" | "linkFor"> => {
    const linkFor = (asset: Asset): string => {
      const absTarget = absPathFor(asset);
      if (!absTarget) return `./${assetId(asset)}.md`;
      return relative(dirname(fromFile), absTarget).replace(/\\/g, "/");
    };

    const fileSpecific: Pick<TemplateContext, "textureUrl" | "render" | "insert" | "linkFor"> = {
      textureUrl: makeTextureUrl(fromFile, rpDir, attachmentsDir),
      linkFor,
      render: () => "",  // filled below
      insert: () => "",  // filled below
    };

    fileSpecific.render = (asset: Asset): string => {
      for (const [stem, assets] of collections) {
        if (assets.includes(asset)) {
          const t = templateMap.get(stem);
          if (!t) return `<!-- no template for collection "${stem}" -->`;
          return renderTemplate(t.src, { ...baseCtx, ...fileSpecific, current: asset });
        }
      }
      return `<!-- asset not found in any collection -->`;
    };

    fileSpecific.insert = (pathOrGlob: string, absorb = true): string => {
      if (isGlob(pathOrGlob)) {
        // Glob → read already-rendered files from outputDir, rewrite paths
        const files = syncGlob(pathOrGlob, config.outputDir);
        if (!files.length) {
          console.warn(`  ⚠️  insert glob matched nothing: ${pathOrGlob}`);
          return `<!-- insert: no files matched "${pathOrGlob}" -->`;
        }
        return files.map((srcFile) => {
          if (absorb) absorbedOutPaths.add(srcFile);
          const content = readFile(srcFile);
          return content ? rewritePaths(content, srcFile, fromFile) : "";
        }).filter(Boolean).join("\n\n");
      }

      // Specific path → read from templateDir, render inline
      if (absorb) absorbedOutPaths.add(join(config.outputDir, normTplPath(pathOrGlob)));
      const absPath = join(config.templateDir, pathOrGlob);
      const raw = readFile(absPath);
      if (!raw) {
        console.error(`  ⚠️  insert target not found: ${absPath}`);
        return `<!-- insert not found: ${pathOrGlob} -->`;
      }
      return renderTemplate(raw, { ...baseCtx, ...fileSpecific, current: null });
    };

    return fileSpecific;
  };

  const baseCtx: TemplateContext = {
    ...ctx,
    addon,
    textureUrl: () => "",   // stub — always overridden per file
    linkFor: () => "",      // stub — always overridden per file
    render: () => "",       // stub — always overridden per file
    insert: () => "",       // stub — always overridden per file
  };

  // ── Phase 1: render + write generated (per-asset) files ───────────────────
  // Write immediately so Phase 2's glob inserts can find them.
  console.log("\n📝 Phase 1 — template expansion\n");
  const seenOut = new Set<string>();

  for (const [stem, assets] of collections) {
    const t = templateMap.get(stem);
    if (!t) continue;
    for (const asset of assets) {
      const outPath = join(config.outputDir, t.subDir, `${assetId(asset)}.md`);
      if (seenOut.has(outPath)) continue;
      seenOut.add(outPath);
      const content = renderTemplate(t.src, { ...baseCtx, ...makeFileCtx(outPath), current: asset });
      write(outPath, content);
    }
  }

  // Remove .template.md originals from outputDir
  for (const t of templates) {
    if (t.isGenerated) {
      try { Deno.removeSync(join(config.outputDir, t.relPath)); } catch { /* ok */ }
    }
  }

  // ── Phase 2: render static files ─────────────────────────────────────────
  // Generated files are on disk; glob inserts now work.
  console.log("\n📝 Phase 2 — static rendering\n");
  const pending: Array<{ outPath: string; content: string }> = [];

  for (const t of templates) {
    if (t.isGenerated) continue;
    const src = readFile(t.absPath);
    if (!src) continue;
    const outPath = join(config.outputDir, t.relPath);
    const content = renderTemplate(src, { ...baseCtx, ...makeFileCtx(outPath) });
    pending.push({ outPath, content });
  }

  let written = 0;
  for (const { outPath, content } of pending) {
    if (absorbedOutPaths.has(outPath)) continue;
    write(outPath, content);
    written++;
  }

  // Remove absorbed files (their content was inlined via insert())
  for (const absPath of absorbedOutPaths) {
    try { Deno.removeSync(absPath); } catch { /* ok */ }
  }

  // Remove any directories left empty by absorption
  pruneEmptyDirs(config.outputDir);

  console.log(`\n✅ Done. ${seenOut.size + written} files written.`);
}
