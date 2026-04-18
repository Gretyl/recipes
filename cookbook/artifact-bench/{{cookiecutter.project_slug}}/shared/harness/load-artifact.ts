// Loads an artifact.html into a jsdom Window with the Claude storage
// API mocked. Call from unit.spec.ts to assert against the rendered
// DOM and any module-level side effects of the inline scripts.

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { JSDOM, type ConstructorOptions } from "jsdom";
import { StorageMock } from "./storage-mock.js";

export interface LoadedArtifact {
  dom: JSDOM;
  window: JSDOM["window"];
  document: Document;
  storage: StorageMock;
}

export interface LoadOptions {
  /** Set to false to skip executing inline scripts (useful for static-only DOM checks). */
  runScripts?: boolean;
}

export function loadArtifact(
  artifactDir: string,
  opts: LoadOptions = {},
): LoadedArtifact {
  const html = readFileSync(
    resolve(artifactDir, "artifact.html"),
    "utf8",
  );
  const storage = new StorageMock();
  const jsdomOpts: ConstructorOptions = {
    runScripts: opts.runScripts === false ? undefined : "dangerously",
    pretendToBeVisual: true,
    url: "https://artifact.test/",
  };
  const dom = new JSDOM(html, jsdomOpts);
  // Expose the mock on the window so artifact code can reach it via
  // window.storage exactly as it does inside Claude.
  (dom.window as unknown as { storage: StorageMock }).storage = storage;
  return {
    dom,
    window: dom.window,
    document: dom.window.document,
    storage,
  };
}
