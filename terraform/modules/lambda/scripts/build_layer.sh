#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

SOURCE_DIR="${1:-.}"
BUILD_DIR="${2:-.build}"
ARCH="${4:-x86_64}"

LAYER_DIR="${BUILD_DIR}/layer/python"
REQUIREMENTS="${BUILD_DIR}/requirements.txt"
PLATFORM="x86_64-unknown-linux-gnu"
[[ "$ARCH" =~ (arm64|aarch64) ]] && PLATFORM="aarch64-unknown-linux-gnu"

mkdir -p "$BUILD_DIR"

# Generate requirements.txt from pyproject.toml (no-dev)
uv export --directory "$SOURCE_DIR" --no-dev --no-hashes -o "$REQUIREMENTS" || uv pip compile "$SOURCE_DIR/pyproject.toml" -o "$REQUIREMENTS"

# Install dependencies into Lambda layer structure
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR"
uv pip install -r "$REQUIREMENTS" --target "$LAYER_DIR" --python-platform "$PLATFORM"

# Clean up bytecode and caches
find "$LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$LAYER_DIR" -type f -name "*.py[co]" -delete 2>/dev/null || true
