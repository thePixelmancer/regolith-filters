```js template entities
return addon.entities.all();
```

## {{this.displayName}}

`{{this.id}}`

{{this.docstring.description}}
{{this.docstring.tags.warning ? `> ⚠️ **Warning:** ${this.docstring.tags.warning.description}` : ''}}
{{this.docstring.tags.note    ? `> 📝 **Note:** ${this.docstring.tags.note.description}`       : ''}}
{{this.docstring.tags.guide   ? `> 📖 **Guide:** ${this.docstring.tags.guide.description}`     : ''}}

```js eval
if (!this.lootTables?.length) return "";
const seen = new Set();
const linked  = this.lootTables.flatMap(t => t.items).filter(i => {
  if (seen.has(i.id)) return false;
  seen.add(i.id);
  return true;
});
const allIds   = [...new Set(this.lootTables.flatMap(t => t.itemIds))];
const unlinked = allIds.filter(id => !seen.has(id));
const lines = [
  ...linked.map(i   => `- ${i.displayName} \`${i.id}\``),
  ...unlinked.map(id => `- \`${id}\``),
];
if (!lines.length) return "";
return `### Drops\n\n${lines.join("\n")}`;
```

```js eval
if (!this.spawnRule?.biomeTags?.length) return "";
return `### Spawns in\n\n${this.spawnRule.biomeTags.map(t => `\`${t}\``).join(", ")}`;
```

```js eval
if (!this.soundEvents?.length) return "";
const rows = this.soundEvents.map(e => `| \`${e.event}\` | \`${e.definitionId}\` |`).join("\n");
return `### Sound Events\n\n| Event | Sound ID |\n|---|---|\n${rows}`;
```
