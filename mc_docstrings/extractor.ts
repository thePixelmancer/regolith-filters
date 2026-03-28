import { parse } from "comment-parser";

interface TagEntry {
  name: string;
  value: string;
}

interface JSDocEntry {
  boundToKey: string;
  description: string;
  tags: Record<string, TagEntry[]>;
}

export async function extractJSDocs(filePath: string): Promise<JSDocEntry[]> {
  const content = await Deno.readTextFile(filePath);
  const results: JSDocEntry[] = [];
  const docRegex = /\/\*\*[\s\S]*?\*\//g;
  let match;

  while ((match = docRegex.exec(content)) !== null) {
    const docEnd = match.index + match[0].length;
    const afterDoc = content.slice(docEnd);
    const keyMatch = afterDoc.match(/^\s*"([^"]+)"\s*:/);
    if (!keyMatch) continue;

    const parsed = parse(match[0]);
    if (!parsed.length) continue;

    const { description, tags: rawTags } = parsed[0];
    const tags: Record<string, TagEntry[]> = {};

    for (const tag of rawTags) {
      if (!tags[tag.tag]) tags[tag.tag] = [];
      tags[tag.tag].push({
        name: tag.name ?? "",
        value: tag.description.trim(),
      });
    }

    results.push({
      boundToKey: keyMatch[1],
      description: description.trim(),
      tags,
    });
  }

  return results;
}
