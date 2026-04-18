// Tiny static-file server for the playwright webServer command.
// Serves public/ on 127.0.0.1:4173 with no caching so e2e specs see
// fresh build output on every run.

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";

const ROOT = resolve("public");
const PORT = 4173;

const TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
};

const server = createServer(async (req, res) => {
  const urlPath = decodeURIComponent((req.url ?? "/").split("?")[0]);
  const safe = normalize(join(ROOT, urlPath)).replace(/\\/g, "/");
  if (!safe.startsWith(ROOT)) {
    res.writeHead(403).end("Forbidden");
    return;
  }
  let target = safe;
  try {
    const s = await stat(target);
    if (s.isDirectory()) target = join(target, "index.html");
  } catch {
    res.writeHead(404).end("Not Found");
    return;
  }
  try {
    const body = await readFile(target);
    res.writeHead(200, {
      "Content-Type": TYPES[extname(target)] ?? "application/octet-stream",
      "Cache-Control": "no-store",
    });
    res.end(body);
  } catch {
    res.writeHead(404).end("Not Found");
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`serve: http://127.0.0.1:${PORT}/ (root=${ROOT})`);
});
