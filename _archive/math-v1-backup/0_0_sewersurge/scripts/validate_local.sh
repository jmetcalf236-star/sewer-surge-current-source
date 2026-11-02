#!/usr/bin/env bash
set -euo pipefail
SDK_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
GAME_DIR="$SDK_ROOT/games/0_0_sewersurge"
cd "$SDK_ROOT"
export PYTHONPATH="$GAME_DIR:$SDK_ROOT${PYTHONPATH:+:$PYTHONPATH}"

python -m pytest "$GAME_DIR/tests" -q

# Debug-only smoke generation. Do not invoke execute_all_tests here: that
# verifier evaluates final RTP/volatility and the deliberately forced,
# unoptimized smoke distributions are expected to fail those release gates.
python "$GAME_DIR/run.py" \
  --sims "${SEWER_SURGE_SMOKE_SIMS:-1000}" \
  --threads "${SEWER_SURGE_THREADS:-1}" \
  --batch-size "${SEWER_SURGE_BATCH_SIZE:-1000}" \
  --compress --clean

for mode in base ante bonus super_bonus; do
  python "$GAME_DIR/scripts/audit_books.py" \
    "$GAME_DIR/library/publish_files/books_${mode}.jsonl.zst"
done

printf '\nDebug smoke generation and four-mode structural audits complete. This is not production verification.\n'
