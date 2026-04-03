```js template items
return addon.items.all();
```

```js eval
const cellLabel   = (cell) => cell ? (cell.texture?.id ? `<img src="${textureUrl(cell.texture?.id)}" alt="${cell.displayName}" width="40" height="40" style="image-rendering: pixelated; vertical-align: middle;">` : `\`${cell.id}\``) : "&nbsp;";
const resultLabel = (r)    => r    ? (r.texture?.id ? `<img src="${textureUrl(r.texture?.id)}" alt="${r.displayName}" width="40" height="40" style="image-rendering: pixelated; vertical-align: middle;"> ×${r.count}` : `\`${r.id}\` ×${r.count}`) : "—";
return { cellLabel, resultLabel };
```

## {{this.displayName}}

`{{this.id}}`{{this.texture?.id ? ` &nbsp; <img src="${textureUrl(this.texture?.id)}" alt="${this.displayName}" width="40" height="40" style="image-rendering: pixelated; vertical-align: middle;">` : ''}}

{{this.docstring.description}}
{{this.docstring.tags.warning ? `> ⚠️ **Warning:** ${this.docstring.tags.warning.description}` : ''}}
{{this.docstring.tags.note    ? `> 📝 **Note:** ${this.docstring.tags.note.description}`       : ''}}
{{this.docstring.tags.guide   ? `> 📖 **Guide:** ${this.docstring.tags.guide.description}`     : ''}}

```js eval
return (this.recipes ?? [])
  .filter(r => r.type === "shaped")
  .map(recipe => {
    const grid = recipe.resolveShape();
    if (!grid) return "";
    const cols = grid[0].length;
    const rows = grid.length;
    const tableHtml = `<table style="border-collapse: collapse; display: inline-block; margin: 10px 0;"><tbody>${
      grid.map(row => `<tr>${
        row.map(cell => `<td style="border: 1px solid #ccc; padding: 2px; text-align: center; width: 44px; height: 44px; vertical-align: middle;">${cellLabel(cell)}</td>`).join('')
      }</tr>`).join('')
    }</tbody></table>`;
    return `### Crafting → ${resultLabel(recipe.result)}\n\n${tableHtml}`;
  })
  .join("\n\n");
```

```js eval
return (this.recipes ?? [])
  .filter(r => r.type === "shapeless" && r.ingredients?.length)
  .map(recipe =>
    `### Crafting (Shapeless) → ${resultLabel(recipe.result)}\n\n` +
    recipe.ingredients.map(i => `- ${cellLabel(i)}`).join("\n")
  )
  .join("\n\n");
```

```js eval
return (this.recipes ?? [])
  .filter(r => r.type === "furnace")
  .map(recipe =>
    `### Smelting → ${resultLabel(recipe.result)}\n\n` +
    `${cellLabel(recipe.ingredients[0])} → ${resultLabel(recipe.result)}`
  )
  .join("\n\n");
```

```js eval
if (!this.entities?.length) return "";
return "### Dropped by\n\n" +
  this.entities.map(e => `- ${e.displayName} \`${e.id}\``).join("\n");
```

```js eval
if (!this.droppedByBlocks?.length) return "";
return "### Dropped by blocks\n\n" +
  this.droppedByBlocks.map(b => `- ${b.displayName} \`${b.id}\``).join("\n");
```
