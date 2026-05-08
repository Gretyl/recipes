#!/usr/bin/env bash
# Regenerate charts/ from data/. Re-run after editing the CSVs.
set -euo pipefail
cd "$(dirname "$0")"

uv run --extra dev chartroom bar \
  --csv data/story_format_features.csv \
  -x format -y feature_score \
  --title "Twine 2 story-format feature support (out of 7)" \
  --xlabel "Story format" \
  --ylabel "Features supported" \
  -o charts/story_format_tradeoffs.png

uv run --extra dev chartroom bar \
  --csv data/form_primitive_usage.csv \
  -x form -y primitives_used \
  --title "Mechanical primitives used by each narrative form (out of 8)" \
  --xlabel "Form" \
  --ylabel "Primitives used" \
  -o charts/form_macro_coverage.png

echo "✓ regenerated charts in $(pwd)/charts/"
