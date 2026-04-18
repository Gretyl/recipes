// Reads docs/manifest.yml and emits public/index.html — the gallery
// landing page that links every artifact described in the manifest.

import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { load } from "js-yaml";

interface ManifestEntry {
  title: string;
  route: string;
  tags?: string[];
  description?: string;
}

interface Manifest {
  artifacts: ManifestEntry[];
}

const raw = readFileSync(join("docs", "manifest.yml"), "utf8");
const manifest = (load(raw) ?? { artifacts: [] }) as Manifest;
const entries = manifest.artifacts ?? [];

const tiles = entries
  .map(
    (e) => `    <li><a href="${e.route}"><strong>${e.title}</strong></a>${
      e.description ? ` &mdash; ${e.description}` : ""
    }</li>`,
  )
  .join("\n");

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Artifacts</title>
  </head>
  <body>
    <h1>Artifacts</h1>
    <ul>
${tiles || "    <li><em>no artifacts yet</em></li>"}
    </ul>
  </body>
</html>
`;

mkdirSync("public", { recursive: true });
writeFileSync(join("public", "index.html"), html, "utf8");
console.log(`gallery: wrote public/index.html (${entries.length} entries)`);
