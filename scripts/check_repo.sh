#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Validating visa_data.json format..."
python3 -m json.tool visa_data.json > /tmp/visa_data_check.json

echo "[2/3] Running git diff --check..."
git diff --check

echo "[3/3] Scanning key user-facing files for Paradiso 39 regressions..."
KEY_FILES=(
  "index.html"
  "ai.html"
  "visa_data.json"
  "moonshot_backend_fastapi.py"
)

if rg -n -e "Paradiso 39" -e "PARADISO 39" -e "paradiso 39" -e "Paradiso39" -e "PARADISO39" -e "paradiso39" "${KEY_FILES[@]}"; then
  echo "ERROR: Found Paradiso 39 regression string(s) in key user-facing files." >&2
  exit 1
fi

echo "Success: repository validation passed. JSON is valid, git diff check is clean, and no Paradiso 39 regressions were found in key user-facing files."
