# Max-win migration inventory (read-only)

No production file was changed. This inventory covers active Sewer Surge math
source and the staged/archived v4 submission metadata. Individual generated book
and LUT records are not listed row by row. The current config's actual cap is
50,000×; the entries below are stale 10,000× wording/data that should be reviewed
before any later production changes.

## Active source and generated audit output

| File | Line(s) | Observed hard-coded value | Status |
|---|---:|---|---|
| `math-sdk/games/0_0_sewersurge/game_config.py` | 133 | Comment says `10,000x remains the per-round max` | Stale comment; config value at line 27 is 50,000×. |
| `math-sdk/games/0_0_sewersurge/scripts/audit_all_modes.py` | 180, 182 | Warnings mention a weighted `10,000x` outcome and its rarity | Stale audit wording; the active audit's numeric cap is 50,000×. |
| `math-sdk/games/0_0_sewersurge/library/audit-summary.json` | 34, 74, 110, 146 | `max_payout_x: 10000.0` | Generated audit output still records old cap. |
| same `audit-summary.json` | 53 | Warning says the `10,000x outcome` is rarer than guideline | Generated audit warning for old cap. |

The active sources currently use the new cap at `game_config.py:27`,
`scripts/audit_all_modes.py:25-26`, and `scripts/audit_books.py:18` (5,000,000
cents). These are listed here to distinguish the current cap from stale 10,000×
references; none was modified.

## Archived math v4 package

| File | Line(s) | Observed hard-coded value | Status |
|---|---:|---|---|
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/config.json` | 32, 57, 82, 107 | `maxWin: 10000.0` | Historical v4 portal config. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/config_fe_0_0_sewersurge.json` | 20, 27, 34, 41 | `max_win: 10000.0` | Historical v4 frontend config. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/math_config.json` | 8, 14, 20, 26 | `max_win: 10000.0` | Historical per-mode math caps. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/math_config.json` | 34-40, 112-118, 190-196, 226-232 | Wincap means and win-range entries use `10000` | Historical optimizer distributions built around old cap. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/event_config_base.json` | 284 | `amount: 1000000` | Historical event payout amount in cents; 1,000,000 cents = 10,000×. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/event_config_ante.json` | 285 | `amount: 1000000` | Same historical cap. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/event_config_bonus.json` | 290 | `amount: 1000000` | Same historical cap. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/configs/event_config_super_bonus.json` | 293 | `amount: 1000000` | Same historical cap. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/stats_summary.json` | 6, 31, 56, 81 | `max_win: 1000000.0` | Historical cent-denominated statistics; 1,000,000 cents = 10,000×. |
| `sewer-surge-submission/upload/math-v4/legacy-math-end-2026-11-01/audit-summary.json` | 34, 74, 110, 146 | `max_payout_x: 10000.0` | Historical audit output. |

The targeted source scan also checked the current math package and the staged
math-v4/math-v5 metadata for `10,000x`, `10,000×`, `10000x`, `10000×`, numeric
`10000`, and `1,000,000`/`1000000` forms. No stale max-win entry was found in the
staged math-v5 metadata. Generated books/LUT values are excluded because they are
individual outcomes, not cap declarations.
