export async function writeItemDocs(items: any[]) {
  await Deno.mkdir("BP/docs/items", { recursive: true });

  for (const item of items) {
    await Deno.writeTextFile(
      `BP/docs/items/${item.identifier}.md`,
      item.content
    );
  }
}

export async function writeIndex(content: string) {
  await Deno.mkdir("BP/docs", { recursive: true });
  await Deno.writeTextFile("BP/docs/index.md", content);
}