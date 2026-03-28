export async function extractFirstJSDoc(filePath: string) {
  try {
    const content = await Deno.readTextFile(filePath);

    const match = content.match(/\/\*\*[\s\S]*?\*\//);

    return match ? match[0] : null;
  } catch {
    return null;
  }
}