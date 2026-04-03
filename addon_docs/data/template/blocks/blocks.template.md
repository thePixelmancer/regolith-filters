```js template blocks
return addon.blocks.all();
```

### {{this.displayName}}

`{{this.id}}`{{this.texture?.id ? ` &nbsp; <img src="${textureUrl(this.texture?.id)}" alt="${this.displayName}" width="40" height="40" style="image-rendering: pixelated; vertical-align: middle;">` : ''}}

{{this.docstring.description}}
{{this.docstring.tags.warning ? `> ⚠️ **Warning:** ${this.docstring.tags.warning.description}` : ''}}
{{this.docstring.tags.note    ? `> 📝 **Note:** ${this.docstring.tags.note.description}`       : ''}}
{{this.docstring.tags.guide   ? `> 📖 **Guide:** ${this.docstring.tags.guide.description}`     : ''}}

```js eval
if (!this.lootTable) return "";
const linked    = this.lootTable.items;
const linkedIds = new Set(linked.map(i => i.id));
const unlinked  = this.lootTable.itemIds.filter(id => !linkedIds.has(id));
const lines = [
  ...linked.map(i    => `- ${i.displayName} \`${i.id}\``),
  ...unlinked.map(id => `- \`${id}\``),
];
return `#### Drops\n\n${lines.join("\n")}`;
```

```js eval
if (!this.soundEvents?.length) return "";
const rows = this.soundEvents.map(e => `| \`${e.event}\` | \`${e.definitionId}\` |`).join("\n");
return `#### Sound Events\n\n| Event | Sound ID |\n|---|---|\n${rows}`;
```
