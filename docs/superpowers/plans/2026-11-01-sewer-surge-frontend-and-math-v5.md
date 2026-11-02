# Sewer Surge Frontend and Math v5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Ship a responsive Sewer Surge screen inspired by the supplied sewer artwork, and stage separately audited math v5 with a 50,000× base-wager cap across all four bet modes.

**Architecture:** Keep the current official Stake Engine Svelte 5/RGS flow and make the illustrated environment decorative, with the live pipe board and game state rendered in Svelte. Regenerate math from the canonical local game source into a separate v5 staging directory, audit it, then update the upload-ready `math-end` package without replacing archived v4 artifacts.

**Tech Stack:** Stake Engine Web SDK, Svelte 5, PixiJS SDK shell, Vite build; Stake Engine Math SDK (pinned Python runtime and Rust optimizer); generated static art assets.

**Spec:** `docs/superpowers/specs/2026-11-01-sewer-surge-frontend-design.md`

## Global Constraints

- Preserve the official SDK RGS, bet actor, resume, and sound flows.
- Keep the board 5×5 with `I`, `L`, `T`, `X`, `W`, and `S`; 3 scatters trigger Bonus and 4–5 trigger Deep Run.
- Branch taps change only the local visual route; the server response remains authoritative for board, feature, and payout.
- The max payout target is 50,000× the base-game wager across Base, Ante, Bonus, and Super Bonus.
- Preserve v4 artifacts; create a distinct v5 artifact set. Publish only after the v5 audit passes.
- Keep the existing costs at 1×, 3×, 100×, and 500× and the target RTP at 96.5% unless v5 evidence exposes a math constraint that requires a user decision.
- Active frontend source is `C:\Users\User\Downloads\web-sdk\apps\sewer-surge`; submission output is `sewer-surge-submission\upload`.
- Do not add or run optional tests. The required production math generation/audit and production frontend build are part of the deliverable.

## Review Focus

- RGS returns a 50,000× payout or capped-win event: display the authoritative amount and cap state without truncation or stale 10,000× text.
- RGS returns a resumed round: restore board, payout, scatter tier, and visual route state without starting a new round.
- A player changes a branch: the highlighted path may change, but the payout, book, and RGS state must not.
- Viewport is narrow or short: board remains legible and the SDK's stake, bet-mode, sound, rules, and spin controls remain reachable.
- Reduced motion is enabled: water-flow animation stops while the same game state remains clear.

---

### Task 1: Regenerate math v5 with the 50,000× base-wager cap

**Files:**
- Review/modify: `math-sdk/games/0_0_sewersurge/game_config.py`
- Review/modify: `math-sdk/games/0_0_sewersurge/rules_validation.py`
- Review/modify: `math-sdk/games/0_0_sewersurge/scripts/audit_all_modes.py`
- Run: `math-sdk/games/0_0_sewersurge/scripts/run_production.ps1`
- Create: `sewer-surge-submission/upload/math-v5/`
- Preserve: `sewer-surge-submission/upload/math-v4/`

**Interfaces:**
- Consumes: exact pinned Math SDK at `sewer-surge-submission/SDK_VERSION.txt` and the game source under `math-sdk/games/0_0_sewersurge`.
- Produces: four optimized books, four LUTs, index/configuration, verification sidecars, and audit summary in the distinct v5 package; each mode's payout multiplier is capped at 50,000× the base-game wager.

- [x] Confirm the source `wincap`, payload validator, and audit cap agree at 50,000×. Check that the mode cost is used only for RTP/stake normalization and does not multiply the requested base-wager cap.
- [x] Confirm `math-sdk` is at commit `6e0c69e3a4edc80ca7e59921e31167cb2ca83c59`, the installed runtime is at `0842bb244cb8c15e63af541054710a8082901e2f`, `zstandard==0.23.0`, and Rust/Cargo are available. Those pins and prerequisites are currently present in the workspace.
- [x] Copy the canonical game folder to a temporary sibling under `math-sdk/games` and run that copy's `scripts/run_production.ps1` for 100,000 simulations per mode. Its `--clean` step then cannot remove the canonical source's existing, inconsistent `library` output or any uploaded v4 file.
- [x] Run the SDK contract verifier, optimized four-mode audit at 96.5% RTP ±0.5 points, and payout/cap checks against the newly generated source books and LUTs. Require no index mismatch, structural failure, or mode above 50,000× base wager.
- [x] If a mode cannot reach the target RTP or cap under the existing constraints, stop and present the audit result and tradeoff before frontend cap text or upload staging changes.
- [x] After the checks pass, copy the temporary game's `library/publish_files`, `library/configs`, `audit-summary.json`, and `stats_summary.json` to the distinct `upload/math-v5` package. Keep `upload/math-v4` byte-for-byte unchanged; update `upload/math-end` only after retaining its prior complete contents with the v4 archive.

### Task 2: Create and review the production game-art concept

**Files:**
- Reference: user-provided Sewer Surge image.
- Create assets under: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\static\assets\sewer-surge\`
- Concept/QA outputs: temporary files outside the production asset folder; remove after final review.

**Interfaces:**
- Consumes: the approved design and selected Svelte-over-art direction.
- Produces: a complete desktop screen concept and original environment/symbol art that keeps all changing text and game state available to Svelte.

- [x] Generate a full game-screen concept in the reference's industrial sewer style, keeping central board, payout/scatter indicators, and bottom control rail in the selected hierarchy.
- [x] Review concept for legibility, 5×5 dynamic-board fit, mobile crop, and no baked-in payout/scatter/control text that could conflict with RGS state.
- [x] Generate separable scene/background art and, if necessary, pipe/scatter artwork that supports rotation and dynamic states; do not bake live symbols into the background plate.
- [x] Compare concept against the reference and design spec; get user acceptance before implementing visual layout.

### Task 3: Implement the responsive illustrated Svelte game screen

**Files:**
- Modify: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\src\components\SewerSurgeBoard.svelte`
- Modify: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\src\components\Background.svelte`
- Modify: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\src\game\assets.ts`
- Modify: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\src\game\stateLayout.ts`
- Modify: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\src\game\config.ts`
- Modify: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\src\components\Game.svelte`
- Add art: `C:\Users\User\Downloads\web-sdk\apps\sewer-surge\static\assets\sewer-surge\`
- Build output: `sewer-surge-submission/upload/frontend/`

**Interfaces:**
- Consumes: SDK state in `stateGame.sewerRound`, SDK `UI` controls in `Game.svelte`, and the accepted art assets.
- Produces: one responsive game scene with live RGS-backed board, scatter tier/count, award/cap display, rules, SDK bet controls, and spin interaction.

- [x] Implement the scene frame and background while keeping a clear live-board region; preserve keyboard/screen-reader labels for pipe and scatter cells.
- [x] Restyle the 5×5 pipe/scatter board to match the reference with clear rotation, active water route, scatter markers, and junction affordances. Preserve route-branch interactions as local visuals only.
- [x] Arrange payout and scatter indicators above/around the board and the SDK's actual bet, sound, menu/rules, and spin controls in the bottom rail; do not replace SDK betting or actor logic with local mock controls.
- [x] Update all four SDK bet-mode `max_win` values from 10,000× to the audited 50,000× base-wager cap; replace stale 10,000× rules copy and retain RGS-authoritative payout display.
- [x] Load desktop and portrait scene assets from the static asset directory and layer them behind the SDK Pixi canvas; remove the template background layer and duplicate game-name/logo snippets while retaining the SDK's control layer.
- [x] Add desktop, portrait, narrow, and short-screen layout adjustments plus `prefers-reduced-motion` behavior.
- [x] Run the frontend's production build, copy the static output to `upload/frontend`, and inspect the desktop render in the browser.
- [ ] Inspect the mobile/portrait render in a browser viewport and fix any blocking layout issues.

### Task 4: Reconcile submission documentation and readiness

**Files:**
- Modify: `sewer-surge-submission/README.md`
- Modify: `sewer-surge-submission/CURRENT_STATUS.md`
- Modify: `sewer-surge-submission/FINAL_STATUS.md`
- Update: `sewer-surge-submission/SDK_VERSION.txt` only if the verified runtime pin changes.

**Interfaces:**
- Consumes: final v5 audit output and successful frontend production build.
- Produces: accurate description of the staged artifact versions and outstanding external blockers.

- [x] Record 50,000× as the maximum only with the v5 audit evidence; report the tested RTP and exact artifact paths.
- [x] Replace any stale maximum-win statistics with values derived from the v5 audit; keep the 96.5% RTP and mode-cost data consistent with generated configs.
- [x] Preserve provider number, final game ID, exact upstream Web SDK pin, and live RGS launch as unresolved blockers unless evidence for them exists.
- [x] Confirm the upload directory contains the frontend build and v5 `math-end` artifacts while the separate v4 archive remains unchanged.


## Execution status

Math v5 generation/audit, frontend implementation, production build, desktop browser review, and upload staging are complete. Mobile-specific CSS is implemented, but a portrait viewport could not be set in the available in-app browser, so visual mobile QA remains open. The RGS UI stays authoritative, and a live session is still required for control and round-flow verification.
