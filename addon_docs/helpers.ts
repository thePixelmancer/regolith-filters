/**
 * helpers.ts
 *
 * Utility functions available in js template and js define blocks.
 *
 * docstring() — normalize a bedrock-kit asset's .documentation into an easy object
 */

import type { Docstring } from "./types.ts";

// ─── docstring() ─────────────────────────────────────────────────────────────

/**
 * Normalizes the first JSDoc block from a bedrock-kit asset's `.documentation`
 * array into an easy-to-navigate Docstring object.
 *
 * Accepts `undefined` or any non-conforming value and returns an empty object,
 * so it is always safe to call.
 *
 * @example
 * ```ts
 * // In a js template block — filtering a collection
 * addon.blocks.filter(b => docstring(b.docstrings).tags.important?.name === "true").all()
 * ```
 */
export function docstring(docs: unknown): Docstring {
  const empty: Docstring = { description: "", tags: {} };
  if (!Array.isArray(docs) || docs.length === 0) return empty;

  const block = docs[0];
  if (typeof block !== "object" || block === null) return empty;

  const description = typeof block.description === "string" ? block.description.trim() : "";
  const tags: Docstring["tags"] = {};

  if (Array.isArray(block.tags)) {
    for (const spec of block.tags) {
      if (typeof spec?.tag !== "string") continue;
      if (tags[spec.tag] !== undefined) continue; // first occurrence wins
      tags[spec.tag] = {
        name: typeof spec.name === "string" ? spec.name : "",
        description: typeof spec.description === "string" ? spec.description.trim() : "",
      };
    }
  }

  return { description, tags };
}
