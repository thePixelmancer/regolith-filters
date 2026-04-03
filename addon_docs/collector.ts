/**
 * collector.ts
 *
 * Builds a CollectionMap and TemplateContext from the asset arrays produced
 * by each template's `js collection` block. Stamps `.docstring` on every asset.
 */

import { docstring } from "./helpers.ts";
import type { Asset, CollectionMap, TemplateContext } from "./types.ts";

/**
 * Stamps a normalized `.docstring` onto an asset if it doesn't already have one.
 * - bedrock-kit assets: reads from `.docstrings`
 * - Entity (logical view): falls back to `.behavior.docstrings`
 * - RawFileAsset (fromGlob): already has `.docstring`, skipped
 */
function stampDocstring(asset: Asset): void {
  if ("docstring" in asset) return;
  const a = asset as Record<string, unknown>;
  const docs = a.docstrings ??
    (a.behavior as Record<string, unknown> | undefined)?.docstrings;
  a.docstring = docstring(docs);
}

export function buildContext(
  rawCollections: Record<string, Asset[]>,
): { ctx: TemplateContext; collections: CollectionMap } {
  const entries = Object.entries(rawCollections) as [string, Asset[]][];

  const collections: CollectionMap = new Map(entries);
  const seen = new Set<Asset>();
  const allAssets: Asset[] = [...collections.values()].flat().filter(a => {
    if (seen.has(a)) return false;
    seen.add(a);
    return true;
  });

  for (const asset of allAssets) {
    stampDocstring(asset);
  }

  const ctx: TemplateContext = {
    ...Object.fromEntries(collections),
    addon: null,           // replaced by renderer
    allAssets,
    current: null,
    render: () => "",      // replaced by renderer
    linkFor: () => "",     // replaced by renderer
    textureUrl: () => "",  // replaced by renderer
    insert: () => "",      // replaced by renderer
  };

  return { ctx, collections };
}
