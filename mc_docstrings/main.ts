import { AddOn, Item, Entity, Biome, Block } from "bedrock-kit";
import { extractJSDocs } from "./extractor.ts";
// Initialize addon
const addon = new AddOn("BP", "RP");

// Fetch items from bedrock-kit
const ITEMS = addon.getAllItems();
const ENTITIES = addon.getAllEntities();
const BIOMES = addon.getAllBiomes();
const BLOCKS = addon.getAllBlocks();


const CONTENT = [ITEMS, ENTITIES, BIOMES, BLOCKS];

for (const content of CONTENT) {
  for (const item of content) {
    if (item instanceof Entity) {
      console.log(await extractJSDocs(item.behaviorFilePath));
    } else {
      console.log(await extractJSDocs(item.filePath));
    }
  }
}
