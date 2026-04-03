/**
 * index.ts — bedrock-doc-gen
 */

import { resolve } from "@std/path";
import { AddOn } from "bedrock-kit";
import { render } from "./renderer.ts";
import type { DocGenConfig } from "./types.ts";

const settings = Deno.args[0] ? JSON.parse(Deno.args[0]) : {};
const ROOT_DIR = Deno.env.get("ROOT_DIR") ?? ".";
const CONFIG: DocGenConfig = {
  outputDir: resolve(ROOT_DIR, settings.outputDir ?? "docs"),
  templateDir: settings.templateDir ?? "data/template",
};

console.log("🔨 bedrock-doc-gen");

const addon = await AddOn.fromDisk("BP", "RP");
render(addon, CONFIG);
