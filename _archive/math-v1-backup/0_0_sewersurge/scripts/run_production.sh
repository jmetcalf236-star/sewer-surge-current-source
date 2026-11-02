#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
GAME_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SDK_ROOT="$(cd -- "${GAME_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON:-python}"
SIMS="${SIMS:-100000}"
THREADS="${THREADS:-10}"
RUST_THREADS="${RUST_THREADS:-10}"
BATCH_SIZE="${BATCH_SIZE:-25000}"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "Python executable not found: $PYTHON_BIN" >&2; exit 2; }
command -v cargo >/dev/null 2>&1 || { echo "Rust/Cargo is required for optimization. Install Rust from https://rustup.rs/" >&2; exit 2; }
command -v rustc >/dev/null 2>&1 || { echo "rustc is required for optimization." >&2; exit 2; }

PY_VER="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$(printf '%s\n' 3.12 "$PY_VER" | sort -V | head -n1)" != "3.12" ]]; then
  echo "Python 3.12 or newer is required; found $PY_VER" >&2
  exit 2
fi

ZSTD_VER="$($PYTHON_BIN -c 'import zstandard; print(zstandard.__version__)' 2>/dev/null || true)"
if [[ "$ZSTD_VER" != "0.23.0" ]]; then
  echo "Pinned zstandard==0.23.0 is required; found '${ZSTD_VER:-not installed}'. Install the Math SDK requirements first." >&2
  exit 2
fi

export PYTHONPATH="${GAME_DIR}:${SDK_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

"$PYTHON_BIN" "$GAME_DIR/scripts/check_sdk_contract.py" --require-exact-pin

"$PYTHON_BIN" "$GAME_DIR/run.py" \
  --sims "$SIMS" \
  --threads "$THREADS" \
  --rust-threads "$RUST_THREADS" \
  --batch-size "$BATCH_SIZE" \
  --compress --clean --optimize --verify

SEWER_SURGE_AUDIT_OUTPUT="$GAME_DIR/library/audit-summary.json" \
  "$PYTHON_BIN" "$GAME_DIR/scripts/audit_all_modes.py" \
  --require-optimized-lut --target-rtp 96.5 --tolerance 0.5

printf '\nSewer Surge production generation, SDK verification and weighted-LUT audit completed.\n'
printf 'Review %s/library/audit-summary.json before any upload.\n' "$GAME_DIR"
