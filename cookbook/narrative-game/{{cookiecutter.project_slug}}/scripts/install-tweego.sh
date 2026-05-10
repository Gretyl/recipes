#!/usr/bin/env bash
#
# install-tweego.sh — idempotent tweego installer for this project.
# Downloads the tweego release archive matching the host platform into
# .tweego/ and verifies the binary runs. Per AGENTS.md
# "Non-Python toolchains" pattern: each setup-<lang> target should be
# safe to run repeatedly.
#
# Override via env vars:
#   TWEEGO_VERSION   tweego release tag (default: 2.1.1)
#   INSTALL_DIR      install destination (default: $PWD/.tweego)

set -euo pipefail

VERSION="${TWEEGO_VERSION:-2.1.1}"
INSTALL_DIR="${INSTALL_DIR:-$(pwd)/.tweego}"
BIN="${INSTALL_DIR}/tweego"

# Idempotent: skip if already present and runnable.
if [ -x "$BIN" ]; then
  # `tweego -v` exits 1, so test it via the file system + an exec probe
  # that ignores -v's exit code — we only care that the binary loads.
  if "$BIN" -v >/dev/null 2>&1 || [ $? -eq 1 ]; then
    echo "✓ tweego already installed at ${BIN}"
    "$BIN" -v || true
    exit 0
  fi
fi

# Detect platform.
OS_RAW="$(uname -s)"
ARCH_RAW="$(uname -m)"

case "$OS_RAW" in
  Linux*)  OS="linux" ;;
  Darwin*) OS="macos" ;;
  *)
    echo "✗ unsupported OS: $OS_RAW (tweego provides linux, macos, windows)" >&2
    exit 1
    ;;
esac

case "$ARCH_RAW" in
  x86_64|amd64) ARCH="x64" ;;
  arm64|aarch64)
    if [ "$OS" = "macos" ]; then
      echo "⚠️  Apple Silicon detected — installing x64 binary (works under Rosetta 2)"
      ARCH="x64"
    else
      echo "✗ tweego does not publish a linux-arm64 binary." >&2
      echo "  Build from source: https://github.com/tmedwards/tweego" >&2
      exit 1
    fi
    ;;
  *)
    echo "✗ unsupported arch: $ARCH_RAW" >&2
    exit 1
    ;;
esac

ARCHIVE="tweego-${VERSION}-${OS}-${ARCH}.zip"
URL="https://github.com/tmedwards/tweego/releases/download/v${VERSION}/${ARCHIVE}"

mkdir -p "$INSTALL_DIR"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "▼ Downloading ${ARCHIVE} from ${URL}"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL -o "${TMPDIR}/${ARCHIVE}" "$URL"
elif command -v wget >/dev/null 2>&1; then
  wget -q -O "${TMPDIR}/${ARCHIVE}" "$URL"
else
  echo "✗ neither curl nor wget found — please install one" >&2
  exit 1
fi

echo "▶ Extracting into ${INSTALL_DIR}"
if ! command -v unzip >/dev/null 2>&1; then
  echo "✗ unzip not found — please install it (apt: unzip / brew: unzip)" >&2
  exit 1
fi
unzip -q -o -d "$INSTALL_DIR" "${TMPDIR}/${ARCHIVE}"

# Defensive: some tweego archives nest the binary under
# tweego-VERSION-OS-ARCH/. Flatten if so.
if [ ! -x "$BIN" ]; then
  NESTED="$(find "$INSTALL_DIR" -maxdepth 3 -name 'tweego' -type f -print -quit)"
  if [ -n "${NESTED:-}" ] && [ "$NESTED" != "$BIN" ]; then
    NESTED_DIR="$(dirname "$NESTED")"
    # shellcheck disable=SC2086
    mv "$NESTED_DIR"/* "$INSTALL_DIR"/
    rmdir "$NESTED_DIR" 2>/dev/null || true
  fi
fi

chmod +x "$BIN"

echo "✓ tweego installed: ${BIN}"
# `tweego -v` exits 1 (it's an informational flag, not an error path),
# so swallow its return value to keep the install script's overall
# exit clean under `set -e`.
"$BIN" -v || true
