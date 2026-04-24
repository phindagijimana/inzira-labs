#!/usr/bin/env bash
# Regenerate Builder Review Word files from bundled Markdown.
# Requires: pandoc (e.g. apt install pandoc)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

build_one() {
  local md=$1
  local out=$2
  if [[ ! -f "$md" ]]; then
    echo "Missing: $md" >&2
    exit 1
  fi
  pandoc "$md" -o "$out" \
    --from markdown \
    --toc --toc-depth=3 \
    --number-sections \
    --standalone
  echo "Wrote $out"
}

build_one "$ROOT/content/EBM_TLE_br.md" "$ROOT/content/EBM_TLE_br.docx"
build_one "$ROOT/content/sustain_br.md" "$ROOT/content/sustain_br.docx"
