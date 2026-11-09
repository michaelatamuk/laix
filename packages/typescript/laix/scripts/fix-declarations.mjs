import { readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const dist = fileURLToPath(new URL("../dist/", import.meta.url));

async function declarationFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await declarationFiles(path)));
    else if (entry.name.endsWith(".d.ts")) files.push(path);
  }
  return files;
}

let changed = 0;
for (const path of await declarationFiles(dist)) {
  const original = await readFile(path, "utf8");
  const text = original
    .replace(/(from\s+["'][^"']+)\.ts(["'])/g, "$1.js$2")
    .replace(/(import\(\s*["'][^"']+)\.ts(["']\s*\))/g, "$1.js$2");
  if (text !== original) {
    await writeFile(path, text, "utf8");
    changed += 1;
  }
}

console.log(`declarations: rewrote ${changed} file(s) to .js import specifiers`);
