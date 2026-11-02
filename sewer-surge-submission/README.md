# Sewer Surge — Stake Engine development candidate

## Active files

- Math source: `math-sdk/games/0_0_sewersurge`
- Audited v5 package: `sewer-surge-submission/upload/math-v5`
- Stake Engine math endpoint package: `sewer-surge-submission/upload/math-end` (mirrors v5)
- Preserved v4 package: `sewer-surge-submission/upload/math-v4`
- Frontend source: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge`
- Frontend static build: `sewer-surge-submission/upload/frontend`
- Stake Engine media: `sewer-surge-submission/media/sewer-surge-game-tile-3x4.svg` (self-contained 3:4 SVG) and `sewer-surge-submission/media/sewer-surge-cover-16x9.png` (1600×900 PNG)
- Older working copies: `_archive` (do not use for release)

This is a locally verified development candidate. Provider approval and live RGS verification have not been completed. Keep the portal-issued provider number and final game ID as release blockers.

## Game specification

- 5×5 pipe board: `I`, `L`, `T`, `X`, and `W`; scatter `S`.
- Base wager: 1×. Ante: 3×. Normal Bonus Buy: 100×. Super Bonus Buy: 500×.
- 0–2 scatters: no feature; exactly 3: Bonus; 4–5: Deep Run.
- Target RTP: 96.5% for each mode.
- Maximum award: 50,000× the base-game wager in every mode.

The RGS/math result supplies the board, rotations, inlet, scatter tier, and award. Junction clicks only change the locally drawn water route. They are not sent to the RGS and cannot change the result.

## Math versions

Math v4 is retained as the earlier 10,000× package in `upload/math-v4`. Math v5 is the current 50,000× package. Production artifacts were generated with 100,000 books per mode (400,000 total) and the pinned EngineIO Math SDK and StakeEngine runtime. The four optimized LUTs audited at 96.5% RTP, with zero structural/LUT failures and a 50,000× maximum payout in every mode. See `upload/math-v5/audit-summary.json` and `upload/math-v5/stats_summary.json`.

Reproduce generation from the Math SDK root on Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\games\0_0_sewersurge\scripts\run_production.ps1 -Simulations 100000 -Threads 10 -RustThreads 10 -BatchSize 25000
```

Use the pinned commits in `SDK_VERSION.txt` and the game's `SDK_PIN.txt`. The published `math-v5` directory is the verified package; `math-end` mirrors it for the existing upload workflow.

## Frontend

The native Svelte 5/Stake Engine app lives in the Web SDK workspace at `C:\Users\User\Downloads\web-sdk\apps\sewer-surge`. It keeps the SDK authentication and betting flow for production, with a development-only preview that skips RGS authentication. The interface uses original landscape and portrait sewer background artwork, a code-rendered pipe board, scatter and payout readouts, an expandable game guide, and SDK betting controls.

The frontend was built with `pnpm build`; its latest static adapter output is staged in `upload/frontend`. A grayscale KingWin chess mark and animated chessboard loader are integrated in the Svelte app; the mark is packaged at `upload/frontend/assets/sewer-surge/kingwin-chess-mark-bw.png`. The previous frontend staging is preserved in `_archive/frontend/upload-frontend-before-kingwin-loader-2026-11-01`. The Web SDK checkout has no Git metadata, so its upstream commit is not recorded. Existing SDK sample audio and other starter assets still need an original-content pass before release.

### Frontend follow-up

The latest frontend aligns award validation with math v5�s 50,000� cap and maps the SDK mode UI to base, ante (3�), bonus (100�), and super bonus (500�). The updated static build is staged in `upload/frontend`.

## Remaining release gates

- Replace placeholder provider number and development game ID when the portal issues production identifiers.
- Run a live RGS session and verify authenticate, bet, resume/replay, and all modes.
- Complete the remaining content/licensing review for retained SDK starter assets.

### Frontend follow-up

The latest frontend aligns award validation with math v5’s 50,000× cap and maps the SDK mode UI to base, ante (3×), bonus (100×), and super bonus (500×). The updated static build is staged in `upload/frontend`.
