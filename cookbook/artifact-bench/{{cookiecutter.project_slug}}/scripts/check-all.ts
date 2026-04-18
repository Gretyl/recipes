// Thin orchestrator: runs the static and runtime gates in order and
// exits non-zero on the first failure. Intended for ad-hoc local
// runs; CI should call `make ci` directly so each step shows up as
// its own job line.

import { spawnSync } from "node:child_process";

const steps: Array<[string, string[]]> = [
  ["npx", ["tsc", "--noEmit", "-p", "tsconfig.json"]],
  ["npx", ["html-validate", "src/**/artifact.html"]],
  ["npx", ["vitest", "run"]],
  ["npx", ["playwright", "test"]],
];

for (const [cmd, args] of steps) {
  console.log(`-> ${cmd} ${args.join(" ")}`);
  const result = spawnSync(cmd, args, { stdio: "inherit" });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
