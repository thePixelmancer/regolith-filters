/**
 * engine.ts
 *
 * Shared eval primitives used by renderer.ts. Not an entry point — import from here.
 */

import { join, dirname, relative } from "@std/path";
import type { Asset, TemplateContext } from "./types.ts";

// ─── Asset ID ────────────────────────────────────────────────────────────────

/** Derives a safe filename/anchor slug from whatever identifier the asset exposes. */
export function assetId(asset: Asset): string {
  const raw = ("id" in asset ? asset.id : "name" in asset ? asset.name : undefined) ?? "unknown";
  return String(raw).replace(/[:/\\]/g, "_").replace(/\s+/g, "-");
}

// ─── Core eval ───────────────────────────────────────────────────────────────

/**
 * Evaluates `code` with the given scope inside an IIFE.
 *
 * When `requireReturn` is false (default), if the IIFE returns undefined and
 * the code has no explicit `return`, it retries as a bare expression — letting
 * callers omit `return` for convenience (used by `js template`).
 *
 * When `requireReturn` is true, the IIFE result is used as-is — an explicit
 * `return` is required (used by `js eval` blocks).
 */
export function evalCode(
  code: string,
  keys: string[],
  vals: unknown[],
  thisVal: unknown,
  requireReturn = false,
): unknown {
  // deno-lint-ignore no-new-func
  const fn = new Function(...keys, `"use strict"; return (() => { ${code} })()`);
  const result = fn.call(thisVal, ...vals);

  if (!requireReturn && result === undefined && !/\breturn\b/.test(code)) {
    // deno-lint-ignore no-new-func
    const fn2 = new Function(...keys, `"use strict"; return (${code.trimEnd().replace(/;$/, "")})`);
    return fn2.call(thisVal, ...vals);
  }

  return result;
}

/** Evaluates code and always returns a string — used by expandInline. */
export function evaluate(code: string, ctx: TemplateContext): string {
  try {
    const result = evalCode(code, Object.keys(ctx), Object.values(ctx), ctx.current);
    if (result == null || result === false) return "";
    if (Array.isArray(result)) return result.filter((r) => r != null).join("");
    return String(result);
  } catch (err) {
    console.error("  ⚠️  eval error:", err);
    return `<!-- eval error: ${err} -->`;
  }
}

// ─── Block processors ────────────────────────────────────────────────────────

/**
 * Processes ` ```js eval ``` ` blocks.
 *
 * - String/array result → inserted as markdown.
 * - Plain object result → merged into context for all subsequent blocks on
 *   this page (no output). Use this to define page-scoped helpers.
 * - null / false / undefined → empty (line dropped by expandInline if solo).
 *
 * Returns the rendered source and the (possibly enriched) context.
 */
export function evalBlocks(src: string, ctx: TemplateContext): [string, TemplateContext] {
  let currentCtx = ctx;
  const rendered = src.replace(/```js\s*eval\s*([\s\S]*?)```/g, (_m, code: string) => {
    try {
      const result = evalCode(code.trim(), Object.keys(currentCtx), Object.values(currentCtx), currentCtx.current, true);
      if (result == null || result === false) return "";
      if (Array.isArray(result)) return result.filter((r) => r != null).join("");
      if (typeof result === "object") {
        // Plain object → merge into running context, produce no output
        currentCtx = { ...currentCtx, ...(result as Record<string, unknown>) } as TemplateContext;
        return "";
      }
      return String(result);
    } catch (err) {
      console.error("  ⚠️  eval error:", err);
      return `<!-- eval error: ${err} -->`;
    }
  });
  return [rendered, currentCtx];
}

/**
 * Expands {{expr}} tokens. If a line consists entirely of a single {{expr}}
 * and it evaluates to empty, the line is dropped so no blank line remains.
 */
export function expandInline(src: string, ctx: TemplateContext): string {
  const lines = src.split("\n");
  const result: string[] = [];
  for (const line of lines) {
    const soloMatch = line.match(/^\s*\{\{([\s\S]+?)\}\}\s*$/);
    if (soloMatch) {
      const val = evaluate(`return (${soloMatch[1].trim()})`, ctx);
      if (val !== "") result.push(line.replace(/\{\{[\s\S]+?\}\}/, val));
      // empty → line dropped entirely
    } else {
      result.push(
        line.replace(/\{\{([\s\S]+?)\}\}/g, (_m, expr: string) =>
          evaluate(`return (${expr.trim()})`, ctx)
        ),
      );
    }
  }
  return result.join("\n");
}

/**
 * Full page render: evaluates all `js eval` blocks (accumulating any context
 * merges), then expands all {{}} inline tokens with the enriched context.
 */
export function renderTemplate(src: string, ctx: TemplateContext): string {
  const [withBlocks, updatedCtx] = evalBlocks(src, ctx);
  return expandInline(withBlocks, updatedCtx);
}

// ─── Named block extractors ──────────────────────────────────────────────────

const TEMPLATE_BLOCK = /```js\s+template\s+(\w+)\s*([\s\S]*?)```/;

/**
 * Extracts and evaluates the `js template <name>` block.
 * Returns [collectionName, assets, srcWithoutBlock].
 * collectionName is the identifier written after `js template` in the tag.
 */
export function evalTemplateBlock(src: string, addon: unknown): [string, Asset[], string] {
  const match = src.match(TEMPLATE_BLOCK);
  if (!match) return ["", [], src];

  const name    = match[1];
  const code    = match[2].trim();
  const stripped = src.replace(TEMPLATE_BLOCK, "").replace(/\n{3,}/g, "\n\n").trimStart();

  try {
    const result = evalCode(code, ["addon"], [addon], null, true);
    if (!Array.isArray(result)) {
      console.error("  ⚠️  js template must return an array");
      return [name, [], stripped];
    }
    return [name, result as Asset[], stripped];
  } catch (err) {
    console.error("  ⚠️  js template eval error:", err);
    return [name, [], stripped];
  }
}

// ─── Texture helper ───────────────────────────────────────────────────────────

/**
 * Returns a textureUrl function that copies referenced textures from rpDir into
 * attachmentsDir (mirroring the RP path structure) and returns a relative path
 * from fromFile to the copied attachment.
 *
 * e.g. texturePath "textures/items/pancake" →
 *   copies  rpDir/textures/items/pancake.png
 *   to      attachmentsDir/textures/items/pancake.png
 *   returns relative path from fromFile to that attachment
 */
export function makeTextureUrl(
  fromFile: string,
  rpDir: string,
  attachmentsDir: string,
): (texturePath: string | undefined) => string {
  return (texturePath) => {
    if (!texturePath) return "";
    const src = join(rpDir, `${texturePath}.png`);
    const dest = join(attachmentsDir, `${texturePath}.png`);
    try {
      Deno.statSync(src);
      Deno.mkdirSync(dirname(dest), { recursive: true });
      try { Deno.statSync(dest); } catch { Deno.copyFileSync(src, dest); }
    } catch { /* source texture not found — return path anyway */ }
    return relative(dirname(fromFile), dest).replace(/\\/g, "/");
  };
}
