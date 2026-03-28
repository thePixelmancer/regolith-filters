import { AddOn } from "npm:bedrock-kit";
import { normalizeDoc } from "./parser.ts";
import { extractFirstJSDoc } from "./extractor.ts";
import { renderItemMarkdown, renderIndex } from "./renderer.ts";
import { writeItemDocs, writeIndex } from "./writer.ts";

// Initialize addon
const addon = new AddOn("BP", "RP");

// Fetch items from bedrock-kit
const items = addon.getAllItems();

const itemsWithDocs = [];

for (const item of items) {
  const filePath = item.filePath;

  if (!filePath) {
    console.warn(`No file path for ${item.identifier}`);
    continue;
  }

  // Extract JSDoc from file
  const jsdoc = await extractFirstJSDoc(filePath);

  const docData = jsdoc ? normalizeDoc(jsdoc) : {};

  const data = {
    id: item.identifier,
    ...docData,
  };

  itemsWithDocs.push({
    ...data,
    content: renderItemMarkdown(data),
  });
}

// Write item markdown files
await writeItemDocs(itemsWithDocs);

// Load template
const template = await Deno.readTextFile("data/templates/index.md");

// Generate index
const indexContent = renderIndex(itemsWithDocs, template);

// Write index file
await writeIndex(indexContent);

console.log(`Generated ${itemsWithDocs.length} item docs`);
