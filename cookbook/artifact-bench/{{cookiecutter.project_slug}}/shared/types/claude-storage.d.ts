// Ambient declarations for the window.storage API exposed inside
// Claude artifacts. Mirrors the shape of the localStorage-like
// interface Claude provides so artifacts that persist data
// typecheck under tsc --checkJs without errors.

interface ClaudeStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  clear(): void;
  readonly length: number;
  key(index: number): string | null;
}

interface Window {
  storage?: ClaudeStorage;
}

declare const storage: ClaudeStorage | undefined;
