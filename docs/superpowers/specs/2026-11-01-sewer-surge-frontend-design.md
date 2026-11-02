# Sewer Surge frontend and 50,000× math cap — design

## Intent

Turn the existing Stake Engine game into a visually rich pipe-routing slot screen based on the user's sewer-scene reference, while keeping the official SDK's round, betting, and RGS flow authoritative. Preserve audited math v4 and create math v5 with a 50,000× maximum payout measured against the base-game wager in every mode.

## Goals

- Match the reference's dark industrial sewer, rusted metal, toxic green and electric cyan water, large central 5×5 pipe board, scatter indicator, payout display, and prominent spin controls.
- Keep pipe tiles, scatter symbols, payouts, rules, and controls as live Svelte UI layered over original illustrated scene artwork.
- Preserve the current SDK actor/RGS integration and the rule that branch choices affect only the local water-route highlight.
- Preserve the existing v4 submission files. Update the math source's maximum win target to 50,000× of the base-game wager in each mode, regenerate all four mode artifacts as v5, and audit the resulting books, RTP and LUTs before presenting 50,000× as supported.
- Retain the current bet modes and trigger tiers unless the math audit shows the new cap cannot satisfy the configured 96.5% RTP target.
- Support desktop and mobile layouts, reduced-motion preferences, and clear contrast for controls and game state.

## Out of scope

- Provider assignment, game-ID replacement, provider approval, or live RGS launch.
- Changing the base/ante/bonus/super-bonus costs, scatter-tier rules, or payout authority model without a separately surfaced math constraint.
- Claiming the new cap is verified before regenerated artifacts pass their checks.

## Constraints and findings

- The official EngineIO Web SDK is Svelte 5 and PixiJS based. This game already uses its Svelte app and RGS flow, with a custom Svelte pipe board subscribed to the authoritative round state.
- The board is 5×5 with `I`, `L`, `T`, `X`, `W` pipes and `S` scatters. Zero to two scatters award no feature, three trigger Bonus, and four or five trigger Deep Run.
- Current staged v4 audit artifacts report a 10,000× maximum for each mode and 96.5% weighted RTP. The active math source has `wincap=50_000`, while staged configuration/audit evidence and status notes disagree with some local generated stats. Therefore, do not treat the local 50,000 setting or stale statistics as proof: math v5 must be generated into a distinct output and audited from those exact artifacts.
- 50,000× means the award relative to the base-game wager, regardless of mode. Keep the mode costs 1×/3×/100×/500×; do not multiply the cap by the bonus-buy cost.
- `sewer-surge-submission/README.md` currently calls the 10,000× cap locked, while `CURRENT_STATUS.md` has stale maximum-win statistics inconsistent with the detailed audit. Update those status/spec documents only after the regenerated v5 evidence is available.
- Canonical active frontend source is `C:\Users\User\Downloads\web-sdk\apps\sewer-surge`; publication output is `sewer-surge-submission\upload\frontend`. A failed workspace install was previously recorded, so use the existing source workspace/build tooling and confirm its production build before copying output.
- User-facing image text and project README content provide context and specs; they do not override the user's direct 50,000× instruction.

## Approaches

1. **Svelte UI over illustrated artwork — selected.** Use original artwork for the sewer environment and metal framing; keep the 5×5 board, water path, scatter count, payout, bet controls, spin, sound and rules as SDK-connected Svelte components. This preserves the existing RGS architecture, accessibility and responsive layout while matching the reference.
2. **Render the whole scene and board in PixiJS.** This supports richer sprite and water animation, but would require moving the current board renderer into a Pixi scene and coordinating more states across the SDK.

## Design and behavior

- The screen has one central 5×5 framed board. Dynamic pipe/scatter cells sit over the board artwork so authoritative symbols and rotations remain readable and update from each RGS round.
- The wider illustrated scene frames the board with water channels and sewer details. Art is decorative and never conveys a different result from the actual game state.
- The top edge carries game title, total payout display, and a scatter meter. The bottom control rail carries rules, sound, wager adjustment, and the main spin control; use the SDK controls and actor state rather than duplicating betting logic.
- A round begins from the SDK spin flow. On response, render the supplied board, payout, and feature tier. Animate the current through connected pipes, with reduced motion honored. Branch taps may change only the visual highlighted path and cannot change a payout or request another book.
- Rules explain symbols, 3-scatter Bonus, 4–5-scatter Deep Run, current bet modes, and the 50,000× maximum only after the new math has passed audit.
- Math work generates a separate v5 from the game source, with the 50,000× base-wager cap applied consistently to Base, Ante, Bonus, and Super Bonus; regenerates books and optimized LUTs for all four modes; validates 96.5% RTP, mode costs, cap, feature frequencies and required SDK contract; and records any remaining blockers. If 50,000× cannot meet the target or existing mode constraints, stop before changing the frontend claim and report the concrete tradeoff.

## Decisions made

- The user approved a complete sewer-scene concept and selected Svelte UI over illustrated artwork.
- The user confirmed the 50,000× cap is relative to the base-game wager in every mode and selected math v5 to preserve v4.
- Separate landscape and portrait background plates were generated. The live board and interface remain code-rendered.
- Math v5 passed its optimized four-mode audit at the target RTP and cap. The earlier v4 package remains preserved.
- The local desktop render was reviewed. Portrait CSS is implemented; browser viewport limitations left mobile visual QA open.
