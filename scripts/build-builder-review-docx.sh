#!/usr/bin/env bash
# Regenerate the Builder Review Word file from the bundled Markdown.
# Requires: pandoc (e.g. apt install pandoc)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MD="$ROOT/content/EBM_TLE_br.md"
OUT="$ROOT/content/EBM_TLE_br.docx"
if [[ ! -f "$MD" ]]; then
  echo "Missing: $MD" >&2
  exit 1
fi
pandoc "$MD" -o "$OUT" \
  --from markdown \
  --toc --toc-depth=3 \
  --number-sections \
  --standalone
echo "Wrote $OUT"
