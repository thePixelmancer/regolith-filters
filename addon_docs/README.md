# Addon-Docs


A [Regolith](https://bedrock-oss.github.io/regolith/) filter that generates Markdown documentation for your Minecraft Bedrock addon. You write templates, it fills them in — one page per item, block, and entity, built from your addon's actual data.

---

## Setup

Add to your Regolith `config.json`:

```json
"filterDefinitions": {
  "mc_docstrings": {
    "runWith": "deno",
    "url": "github.com/Pixelmancer-64/regolith-filters/mc_docstrings"
  }
},
"filters": [
  {
    "filter": "mc_docstrings",
    "settings": {
      "outputDir":   "./build/docs",
      "templateDir": "./data/template"
    }
  }
]
```

| Setting | Default | Description |
|---|---|---|
| `outputDir` | `docs` | Where to write the generated docs |
| `templateDir` | `data/template` | Your template folder |

The output folder is wiped and rebuilt on every run.

---

## Your first template

Create a file called `items.template.md` anywhere in your template folder. The `.template.md` extension is what tells the filter this file generates one page per asset:

````markdown
```js template items
return addon.items.all();
```

## {{this.displayName}}

`{{this.id}}`

{{this.docstring.description}}
````

That's it. Running the filter produces one `.md` file per item, with the item's name, ID, and description filled in automatically.

The `js template items` block is where you choose which assets to generate pages for. `items` is the name you give this collection — that name becomes a variable available in every template and static page. `addon` gives you access to everything in your pack, and is available in all template scopes.

---

## Template files

There are two kinds of files in your template folder:

**`*.template.md`** — generates one page per asset. Put your per-item, per-block, per-entity layouts here.

**`*.md`** — rendered once as a static page. Use these for index pages, changelogs, known issues — anything that doesn't repeat per asset.

Subdirectory structure is preserved in the output:

```
data/template/
  index.md                    →  docs/index.md
  known_issues.md             →  docs/known_issues.md  (or absorbed into index)
  items/
    items.template.md         →  docs/items/mypack_copper_spear.md  (one per item)
  blocks/
    blocks.template.md        →  docs/blocks/mypack_oak_log.md  (one per block)
  entities/
    entities.template.md      →  docs/entities/mypack_goblin.md  (one per entity)
```

---

## What you can write in templates

### `{{expression}}` — output a value inline

Put any JavaScript expression between `{{` and `}}`. `this` refers to the current asset.

```markdown
## {{this.displayName}}

`{{this.id}}`
```

If a line contains only a `{{...}}` and it evaluates to empty or false, **the entire line is removed** — no blank lines left behind. This makes conditional content easy:

```markdown
{{this.docstring.description}}
{{this.docstring.tags.warning ? `> ⚠️ **Warning:** ${this.docstring.tags.warning.description}` : ''}}
{{this.docstring.tags.note    ? `> 📝 **Note:** ${this.docstring.tags.note.description}`       : ''}}
```

If a block has no warning, that line simply doesn't appear.

---

### ` ```js eval ``` ` — a block of JavaScript

For anything more complex than a single value — lists, tables, conditional sections. Always use an explicit `return`.

````markdown
```js eval
if (!this.lootTable) return "";
const lines = this.lootTable.items.map(i => `- ${i.displayName} \`${i.id}\``);
return `### Drops\n\n${lines.join("\n")}`;
```
````

If the block returns nothing (or `""`, `null`, `false`), nothing is inserted.

**Defining helpers for the rest of the page**

If a `js eval` block returns a plain object, its properties become available to all subsequent blocks and `{{}}` expressions on that page. Use this to define formatters or shared values at the top of a template:

````markdown
```js eval
const label = (cell) => cell ? `\`${cell.id}\`` : "&nbsp;";
return { label };
```

```js eval
// label is now available here
return this.recipes.map(r => r.resolveShape()
  .map(row => `| ${row.map(label).join(" | ")} |`)
  .join("\n")
).join("\n\n");
```
````

---

### `insert(path)` — pull in another file

Use `insert()` to bring in content from another file at that point in the document. The inserted file's content replaces the call — it's deleted from the output once inlined (so it doesn't appear twice). Any directories left empty after this are cleaned up automatically.

**Pull in a specific file:**

```markdown
{{insert("./known_issues.md")}}
```

**Pull in all generated files matching a pattern:**

```markdown
{{insert("./items/*.md")}}
```

This inserts every generated item page in one go — useful for building a single combined document. Image paths and links inside the inserted files are automatically adjusted to work from the new location.

**Keep the original file too:**

Pass `false` as the second argument if you want the file to stay in the output as well as be inlined:

```markdown
{{insert("./reference.md", false)}}
```

**Use it inside a `js eval` block** when you need logic alongside it:

````markdown
```js eval
insert("./blocks/*.md");  // absorb the individual files
const wood  = blocks.filter(b => b.docstring.tags.wood !== undefined);
const other = blocks.filter(b => b.docstring.tags.wood === undefined);
const group = (label, list) =>
  list.length ? `## ${label}\n\n${list.map(b => render(b)).join("\n\n")}` : "";
return [group("Wood Blocks", wood), group("Other Blocks", other)].filter(Boolean).join("\n\n");
```
````

Here `insert()` is called to absorb (delete) the generated block files, while `render()` re-renders each block inline in a custom order and grouping.

---

### `render(asset)` — render an asset inline

Renders an asset through its own template and returns the result as a string. Useful when you want to embed an asset's full page inside an index or group view.

```markdown
```js eval
return blocks.map(b => render(b)).join("\n\n");
```
```

---

## Adding descriptions to your addon files

You can write documentation directly in your BP/RP JSON files using `/** */` block comments. The filter reads these automatically and exposes them as `this.docstring` in templates.

```jsonc
/**
 * A spear crafted from raw copper. Deals 5 damage on hit.
 *
 * @warning
 * Loses durability twice as fast in rain.
 * @category weapons
 * @guide
 * See the smithing guide for upgrade paths.
 */
{
  "format_version": "1.21.0",
  "minecraft:item": {
    "description": { "identifier": "mypack:copper_spear" }
  }
}
```

The text before any `@tags` becomes `this.docstring.description`. Each tag becomes a property on `this.docstring.tags`.

**Tag formats:**

```
@tagname
Multi-line description that belongs to this tag.

@category weapons
```

The first word after a tag on the same line becomes its `name` (`@category weapons` → `name: "weapons"`). Everything on the lines below (until the next tag) becomes its `description`. Tags with nothing at all — like `@wood` or `@deprecated` — just mark presence; check for them with `!== undefined`.

**In templates:**

```markdown
{{this.docstring.description}}
{{this.docstring.tags.warning?.description}}
{{this.docstring.tags.category?.name}}
{{this.docstring.tags.wood !== undefined ? "This is a wood block." : ""}}
```

`this.docstring` is always safe to access — if no comment is found, it returns `{ description: "", tags: {} }`.

---

## What's available in templates

| Variable | What it is |
|---|---|
| `this` | The current asset (item, block, entity…). `null` on static pages. |
| `addon` | The full addon object — same as in `js template` blocks. Access any collection: `addon.items`, `addon.blocks`, etc. |
| *(collection name)* | Whatever name you put after `js template` becomes a variable holding that collection's assets. `js template weapons` → `weapons` is available everywhere. |
| `allAssets` | Every asset across all collections combined. |
| `textureUrl(id)` | Copies the texture from the RP and returns a path to it. Pass `this.texture?.id`. |
| `linkFor(asset)` | Returns a relative link to that asset's doc page. |
| `render(asset)` | Renders an asset through its template and returns the result as a string. |
| `insert(path)` | Pulls in another file's content inline. |

**Common asset properties:**

```
this.id            // "mypack:copper_spear"
this.displayName   // "Copper Spear"  (resolved from your lang file)
this.texture?.id   // "textures/items/copper_spear"
this.recipes       // Recipe[]
this.lootTable     // LootTable | undefined  (blocks)
this.entities      // Entity[]  (entities that drop this item)
this.soundEvents   // SoundEventBinding[]
this.docstring     // { description, tags }
```

See the [bedrock-kit API reference](bedrockKitApiRef.md) for the full list per asset type.

---

## Full example

**`data/template/items/items.template.md`** — one page per item:

````markdown
```js template items
return addon.items.all();
```

```js eval
const cellLabel   = (cell) => cell ? `\`${cell.id}\`` : "&nbsp;";
const resultLabel = (r)    => r    ? `\`${r.id}\` ×${r.count}` : "—";
return { cellLabel, resultLabel };
```

## {{this.displayName}}

`{{this.id}}`{{this.texture?.id ? ` &nbsp; <img src="${textureUrl(this.texture?.id)}" alt="${this.displayName}" width="40" height="40" style="image-rendering: pixelated; vertical-align: middle;">` : ''}}

{{this.docstring.description}}
{{this.docstring.tags.warning ? `> ⚠️ **Warning:** ${this.docstring.tags.warning.description}` : ''}}
{{this.docstring.tags.note    ? `> 📝 **Note:** ${this.docstring.tags.note.description}`       : ''}}

```js eval
return (this.recipes ?? [])
  .filter(r => r.type === "shaped")
  .map(recipe => {
    const grid = recipe.resolveShape();
    if (!grid) return "";
    const cols = grid[0].length;
    const head = `| ${Array(cols).fill("").join(" | ")} |`;
    const sep  = `|${Array(cols).fill(" :---: ").join("|")}|`;
    const rows = grid.map(row => `| ${row.map(cellLabel).join(" | ")} |`).join("\n");
    return `### Crafting → ${resultLabel(recipe.result)}\n\n${head}\n${sep}\n${rows}`;
  })
  .join("\n\n");
```

```js eval
if (!this.entities?.length) return "";
return "### Dropped by\n\n" +
  this.entities.map(e => `- ${e.displayName} \`${e.id}\``).join("\n");
```
````

**`data/template/index.md`** — combines everything into one file:

````markdown
# Addon Documentation

{{insert("./known_issues.md")}}

# Items

{{insert("./items/*.md")}}

# Blocks

```js eval
insert("./blocks/*.md");
const wood  = blocks.filter(b => b.docstring.tags.wood !== undefined);
const other = blocks.filter(b => b.docstring.tags.wood === undefined);
const group = (label, list) =>
  list.length ? `## ${label}\n\n${list.map(b => render(b)).join("\n\n")}` : "";
return [group("Wood Blocks", wood), group("Other Blocks", other)].filter(Boolean).join("\n\n");
```

# Entities

{{insert("./entities/*.md")}}
````

The result is a single `docs/index.md` with every item, block, and entity inlined. Blocks are split into two groups based on the `@wood` tag. All intermediate files are cleaned up automatically.
