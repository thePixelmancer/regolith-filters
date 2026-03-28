export function renderItemMarkdown(item: any) {
  return `# ${item.id}

## Description
${item.description || "No description"}

## Usage
${item.usage || "N/A"}

## Notes
${item.notes || "None"}

## Warning
${item.warning || "None"}

## Dev
${item.dev || "None"}

## Group
${item.group || "None"}

## Dependencies
${item.depends || "None"}
`;
}

export function renderIndex(items: any[], template: string) {
  const list = items.map((i) => `- [${i.id}](./items/${i.id}.md)`).join("\n");

  return template.replace("{{items}}", list);
}
