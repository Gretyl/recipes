// Walks src/<artifact>/artifact.html (and src/<category>/<artifact>/artifact.html
// for nested layouts) and copies each into public/ at the path that
// matches its deploy URL. Strips the src/ prefix and the artifact
// directory name so a top-level src/foo/artifact.html lands at
// public/foo.html, and src/tutorials/bar/artifact.html lands at
// public/tutorials/bar.html.

import { readdirSync, mkdirSync, copyFileSync, statSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";

const SRC_ROOT = "src";
const PUBLIC_ROOT = "public";

function isDir(path: string): boolean {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
}

function findArtifactDirs(root: string, depth: number): string[] {
  if (depth < 0 || !isDir(root)) return [];
  const out: string[] = [];
  for (const entry of readdirSync(root)) {
    const path = join(root, entry);
    if (!isDir(path)) continue;
    if (existsSync(join(path, "artifact.html"))) {
      out.push(path);
    } else {
      out.push(...findArtifactDirs(path, depth - 1));
    }
  }
  return out;
}

function deployPath(artifactDir: string): string {
  // src/foo                   -> public/foo.html
  // src/tutorials/how-x       -> public/tutorials/how-x.html
  const rel = artifactDir.replace(/^src[\\/]/, "");
  return join(PUBLIC_ROOT, `${rel}.html`);
}

const artifacts = findArtifactDirs(SRC_ROOT, 2);
for (const dir of artifacts) {
  const target = deployPath(dir);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(join(dir, "artifact.html"), target);
  console.log(`built ${dir} -> ${target}`);
}
console.log(`built ${artifacts.length} artifact(s)`);
