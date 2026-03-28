import { parse } from "npm:comment-parser";

export function normalizeDoc(jsdoc: string) {
  const parsed = parse(jsdoc);
  const doc = parsed[0];

  if (!doc) return {};

  return Object.fromEntries(
    doc.tags.map(tag => [
      tag.tag,
      tag.description
        ?.split("\n")
        .map(l => l.trim())
        .filter(Boolean)
        .join(" ")
    ])
  );
}