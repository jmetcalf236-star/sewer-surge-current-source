# Sewer Surge — Current Status

## Status

Local math v5 generation/audit and the frontend build are complete. Provider/game identifiers and live RGS verification remain pending, so this is not a release-approved package.

## Math v5

- Generated using EngineIO Math SDK `6e0c69e3a4edc80ca7e59921e31167cb2ca83c59` and StakeEngine runtime `0842bb244cb8c15e63af541054710a8082901e2f`.
- 100,000 books per mode; 400,000 total.
- Audit: `optimized math/LUT audit passed`; four optimized LUTs at 96.5% weighted RTP; max payout 50,000× in base, ante, bonus, and super bonus; zero structural/LUT failures or index mismatches.
- Ante/Base combined feature frequency ratio: 4.999994 (target 5.0).
- Package: `upload/math-v5`. `upload/math-end` mirrors it. The earlier v4 package remains under `upload/math-v4`.
- The temporary generation copy `math-sdk/games/_tmp_sewer_surge_v5` remains (~174 MB): automatic review blocked its recursive cleanup. The staged audit references the persistent v5 package paths.

## Frontend

- Source: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge`.
- `pnpm build` emitted the static site and the SvelteKit adapter wrote `build`; the latest output is staged in `upload/frontend`. The wrapper hung after the completion message and was interrupted, so it did not return a clean exit code.
- Added a grayscale KingWin chess mark and animated chessboard loader, shown while SDK assets load; the image is included at `upload/frontend/assets/sewer-surge/kingwin-chess-mark-bw.png`.
- Desktop browser preview showed the illustrated sewer scene, custom board, payout/scatter display, and expanded rules panel. The KingWin loader build is included; the live preview confirmed it dismisses into the game screen.
- Build warnings remain for unset `PUBLIC_*` environment variables and the large shared SDK bundle. No gameplay tests or live RGS checks were run for this frontend change.
- Award validation now matches math v5�s 50,000� cap (5,000,000 hundredths). SDK mode metadata now defines base, ante (3�), bonus (100�), and super bonus (500�) with the math mode names.
- Live RGS controls and round data could not be verified without a session. Production authentication remains enabled; only the local development branch bypasses it for preview.

## External release gates

1. Assign provider number and final game ID; replace `provider_number=0` and development ID `0_0_sewersurge`.
2. Run live RGS verification for authentication, betting, resume/replay, and each mode.
3. Review retained SDK starter audio/assets and replace or clear them as required.

- Follow-up fix: frontend award validation now matches math v5’s 50,000× cap (5,000,000 hundredths). The SDK mode UI now defines base, ante (3×), bonus (100×), and super bonus (500×) using the math mode names. Updated production output is staged in `upload/frontend`. The Vite/SvelteKit build emitted the static site and the adapter wrote `build`; existing warnings remain for unset `PUBLIC_*` variables and the large SDK bundle.


## Local preview verification (2026-11-01)

- `npx vite preview --outDir build --host 127.0.0.1 --port 4174` served the built frontend at `http://127.0.0.1:4174/`.
- The open `3001` dev page was blank because the dev server was not listening; the browser reported a failed dynamic import from `3001`. The `4174` production preview rendered the game.
- Added a dev-only mock RGS at `web-sdk/tools/mock-rgs/server.mjs`, outside the app's `static/` and `build/` directories. It reads the sampled real books and starts sessions at 1,000,000,000 RGS units ($1,000.00).
- The UI exercised `/wallet/authenticate`, `/wallet/play`, `/bet/event`, and `/wallet/end-round`. `/wallet/balance` is also implemented. Bet configuration is returned inside the authenticate response.
- Manual browser interaction verified a zero-award base round, then a 3-scatter round awarding $0.60 at a $0.10 base play, followed by another zero-award round. The zero-award round no longer blocks the next play after the mock lifecycle fix. No new browser console errors appeared during this sequence.
- A streaming validation pass accepted 100,000 generated books in each of base, ante, bonus, and super bonus (400,000 total); each mode had zero rejected books.
- The existing `build/` directory contained 168 files totaling 63,265,499 bytes (60.33 MiB) when measured. Desktop screenshots were captured at 1920x892. The requested 1366x768 and 390x844 screenshot sets, and a complete before/after matrix, have not been captured.

## Pure-slot frontend follow-up (2026-11-01)

- Changed `web-sdk/apps/sewer-surge/src/components/SewerSurgeBoard.svelte`, `PipeSymbol.svelte`, `SewerSurgeWin.svelte`, and `game/sewerSurgeFlow.ts` to remove board inputs, trace every connected pipe branch automatically, stagger water animation, delay the result dialog until flow completes, count the win amount up, and skip the wait/dialog during turbo or autoplay. The board uses `pointer-events: none`; the Rules text describes RGS-determined results and illustrative pipe animation.
- Added `tests/sewerSurgeBoardUi.test.mjs` checks for a non-interactive board, mobile plate sizing, connected junction flow, and normal/fast flow timing. Existing validator rejection of `routeChoice` and the real-book fixture were not changed.
- `npm test` output: 16 tests, 16 passed, 0 failed. The real-book contract subtest passed for 519 sampled books across the four modes.
- `npm run build` completed and wrote `build`. Observed warnings: Svelte unused selectors `.pipe-cell svg`, `.board-footer .connected`, `.board-footer .disconnected`, and `h1`; SDK environment exports `PUBLIC_SITE_MODE`, `PUBLIC_SENTRY_DSN`, and `PUBLIC_CHROMATIC` are missing; the client bundle is 1,120.30 kB (336.63 kB gzip), over the 500 kB warning threshold.
- Local preview at `http://127.0.0.1:4174/` was exercised with the funded mock RGS on port 4302. Browser accessibility output showed no board controls; clicking a board cell at 1920x892 left the round unchanged. A 3-scatter real-book fixture displayed `BONUS RUN`; a 4-scatter junction fixture displayed `DEEP RUN` and lit connected branches.
- Screenshots were viewed at 1920x892, 1366x768, and 390x844. The 390px viewport initially showed horizontal overflow; adding `box-sizing: border-box` to the title, HUD, and board plates brought those elements within the viewport. At mobile size the SDK spin controls remained visible.
- Observed discrepancy: the generated max-win fixture renders a 50,000× award while the updated Rules panel says 10,000×. Math, books, validator, and RGS handling were not changed in this frontend follow-up.

- Additional browser observations: the final 1920x892 accessibility tree has no board buttons, role=button nodes, or focusable board elements (count 0); clicking a board cell left the shown round unchanged. The browser console had no errors, but showed repeated SDK “Uncompiled message detected!” warnings for controls and a Pixi cache warning that `totalwin.png` was already present.
- The requested matrix is not fully isolated in saved screenshot files: captures were viewed interactively at all three sizes, including idle, no-feature, Bonus, Deep Run/junction, and feature dialogs across the sizes; a reproducible mid-flow frame was not captured at every viewport.
