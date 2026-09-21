#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

SOURCE_DIR="${1:-.}"
BUILD_DIR="${2:-.build}"
ARCH="${4:-x86_64}"

LAYER_DIR="${BUILD_DIR}/layer/python"
REQUIREMENTS="${BUILD_DIR}/requirements.txt"
HASH_FILE="${BUILD_DIR}/.layer_hash"
PLATFORM="x86_64-unknown-linux-gnu"
[[ "$ARCH" =~ (arm64|aarch64) ]] && PLATFORM="aarch64-unknown-linux-gnu"

mkdir -p "$BUILD_DIR"

# Compute current manifest hash
CURRENT_HASH=""
if command -v sha256sum &>/dev/null; then
  CURRENT_HASH=$(cat "$SOURCE_DIR/pyproject.toml" "$SOURCE_DIR/uv.lock" 2>/dev/null | sha256sum | awk '{print $1}')
elif command -v shasum &>/dev/null; then
  CURRENT_HASH=$(cat "$SOURCE_DIR/pyproject.toml" "$SOURCE_DIR/uv.lock" 2>/dev/null | shasum -a 256 | awk '{print $1}')
fi

if [[ -d "$LAYER_DIR" && -n "$CURRENT_HASH" && -f "$HASH_FILE" && "$(cat "$HASH_FILE" 2>/dev/null)" == "$CURRENT_HASH" ]]; then
  echo "Lambda layer dependencies are up-to-date. Skipping build."
  exit 0
fi

echo "Building Lambda layer dependencies with uv..."
# Generate requirements.txt from pyproject.toml (no-dev)
uv export --directory "$SOURCE_DIR" --no-dev --no-hashes -o "$REQUIREMENTS" || uv pip compile "$SOURCE_DIR/pyproject.toml" -o "$REQUIREMENTS"

# Install dependencies into Lambda layer structure
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR"
uv pip install -r "$REQUIREMENTS" --target "$LAYER_DIR" --python-platform "$PLATFORM"

# Clean up bytecode and caches
find "$LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$LAYER_DIR" -type f -name "*.py[co]" -delete 2>/dev/null || true

if [[ -n "$CURRENT_HASH" ]]; then
  echo "$CURRENT_HASH" > "$HASH_FILE"
fi

echo "Lambda layer build completed."
