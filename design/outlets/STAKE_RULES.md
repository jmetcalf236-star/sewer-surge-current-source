# Stake Engine rules relevant to the Sewer Surge outlets study

Source: official [`engineio/docs`](https://github.com/engineio/docs), cloned outside
the project at `C:\Users\User\Downloads\engineio-docs-rules-audit`, commit
`fefadc7bd117f8e06f0a01e750408da2244f8d8f`. Quotes below are verbatim from the
repository's `src/` files. Assessments apply to the proposed base-only outlets
presentation; they are not an approval decision.

## Approval and general requirements

**Approval process — unclear until the complete game is reviewed.**

> Before a game can go live on the Stake platform, it must pass a structured approval process covering math validation, frontend quality, RGS integration, jurisdiction compliance, and replay support.

File: `src/routes/docs/approval/+page.svx:15`.

> Use this checklist to track your game's approval progress. All items must be verified before submitting for review.

File: `src/routes/docs/approval/checklist/+page.svx:75`.

**Stateless/chance game — complies if outlet routing is fixed by the pre-generated result.**

> Stake Engine games are strictly *stateless*: Each bet must be independent of previous outcomes. Games cannot include jackpots, gamble features, continuation, or early cashout options.

File: `src/routes/docs/approval/+page.svx:19`.

## Originality, IP, and content

**Originality/IP — unclear for the concept; use original art, title, and assets.**

> Team names, game titles, and assets must comply with intellectual property/copyright law. Infringement is grounds for rejection.

> Games must be original designs. Pre-purchased or licensed games existing on other third-party websites will not be permitted.

File: `src/routes/docs/approval/+page.svx:20-21`.

**Brand/theme restrictions — complies if sewer artwork avoids prohibited content.**

> Game assets cannot include material with Stake™ / Kick™ branding or themes.

> Approval is at the discretion of the reviewer. Games deemed offensive, explicit, in poor taste, or of insufficient quality may be rejected.

> Games that promote, encourage, or are likely to appeal to underage persons are not permitted. This includes artistic depictions of children or child-like characters in any gambling context.

File: `src/routes/docs/approval/+page.svx:22-24`.

## RTP, modes, and buy features

**RTP range — the 96.5% base-only candidates comply with the stated range.**

> The calculated Return to Player (RTP) must be within 90.0%–98.0%. For multiple modes, all must fall within a 0.5% variation (e.g., base game at 97% RTP requires other modes to be between 96.5% and 97.5%).

File: `src/routes/docs/approval/math-requirements/+page.svx:13`.

**RTP variation FAQ — no cross-mode comparison applies to this base-only proposal.**

> Yes. The 0.5% RTP variation rule applies to every mode in your game, regardless of the mechanic.

> All game modes must fall within a 0.5% RTP variation of the base game. For example, if your base game has an RTP of 97.0%, every other mode must be between 96.5% and 97.5%.

File: `src/routes/faq/math/rtp-variation-side-bets/+page.svx:10,14`.

**Conflicting bet-mode description — unclear; use the stricter approval/FAQ requirement pending clarification.**

> Different modes can have entirely different RTP, volatility, and win distributions

File: `src/routes/docs/architecture/how-rgs-works/+page.svx:115`. This conflicts with
the approval requirement and FAQ quoted above, which require a 0.5% variation.

**Bonus-buy treatment — not applicable to this base-only model.**

> This is a flag used for the frontend framework to determine if the mode has been purchased directly (and hence may require a change in assets).

File: `src/routes/docs/math-sdk/setup/betmode/+page.svx:13-14` (`is_buybonus`). The
same page's example configures `cost=100.0` at lines 18-25. **Not found:** a general
buy-price ceiling or a rule requiring bought and naturally triggered features to
have identical distributions.

## Maximum win, rarity, hit rate, and volatility

**Maximum win description — the proposed 50,000× Variant A must be displayed in its rules.**

> Ensure the maximum win amount matches the description in the game rules for each mode.

File: `src/routes/docs/approval/math-requirements/+page.svx:14`.

**Maximum-win rarity — Variant A is judged against the stated typical frequency.**

> The maximum win must be realistically obtainable (typically more frequent than 1 in 10,000,000, depending on payout amount).

File: `src/routes/docs/approval/math-requirements/+page.svx:15`. Under the study's
explicit `P(route reaches an outlet)=0.8` assumption, a 50,000× win paid 1 in 5M is
more frequent than this guideline; 1 in 10M is exactly at the boundary, not more
frequent; 1 in 20M is less frequent and therefore at risk. The docs say “typically”
and “depending on payout amount,” so they do not state an absolute numerical ban.
No separate platform-wide maximum-win ceiling was found in `src/`; the docs do
require that each mode's cap be consistent with its displayed rules. Wincap is
described as per-mode and applied if a win exceeds it:

> Each bet mode has its own wincap, which may differ between modes

> If a player's win exceeds the wincap, the payout is automatically capped

File: `src/routes/docs/architecture/how-rgs-works/+page.svx:104,107`.

**Hit-rate and volatility — the exact table statistics should be reviewed with the math package.**

> A reasonable portion of simulations should yield paying results (e.g., 90,000 non-paying results out of 100,000 may be grounds for rejection).

> The hit-rate of non-zero wins should align with industry standards (<1 in 20 bets, or more frequent).

> For "BASE" modes (1x cost), the standard deviation should be within industry norms to ensure reasonable volatility for slot-type games.

File: `src/routes/docs/approval/math-requirements/+page.svx:17,21-22`. The target
hit rates 30%, 15%, and 5% are at least 1 in 20. The 5% table has 95% losing rounds,
which is above the doc's example of 90% non-paying and is **at risk** under its
“may be grounds for rejection” wording. No numeric volatility bound is specified.

> The hit-rate of the most likely single simulation should not be overwhelmingly dominant if there is a visual expectation that results are sufficiently varied.

> List the number of non-zero weight payouts. Zero-weight payouts should not dominate the provided simulations.

> Inspect hit-rates for win-ranges to avoid gaps where expected win amounts are unobtainable (e.g., intermediate wins should exist between small payouts and the maximum payout amount).

File: `src/routes/docs/approval/math-requirements/+page.svx:18,23-24`.

## Near-miss, player choice, and outcome display

**Near-miss wording — not found. Misleading presentation is addressed generally.**

> Summary statistics and hit-rate tables will be analyzed to ensure the game adheres to industry standards for chance-based casino games and is not misleading.

File: `src/routes/docs/approval/math-requirements/+page.svx:9`. No direct `near-miss`
rule was found in the docs `src/`. Displaying a valuable prize on an outlet the
water does not reach could create a near-miss impression; avoid “almost won” copy,
teasing sounds, or visual emphasis that suggests skill or proximity changed odds.

**Player choice/skill — complies only if the player cannot steer the stream.**

> **No influence on results** - a player cannot affect the outcome through betting strategy, timing, or any other action. The result is determined by RNG and the LUT weights.

File: `src/routes/docs/architecture/how-rgs-works/+page.svx:94`. A single automatic
stream is consistent with this statement. Player-controlled routing would be at
risk. A payout-explaining animation must not determine or alter the award.

**RGS/frontend distinction — prize row, board, and displayed flow must explain the pre-calculated award.**

> Stake Engine uses **pre-calculated game results** - the RGS determines all outcomes before they are displayed. The frontend is purely an animation layer.

> Payouts come from the **server response**, not from visual events in the browser.

File: `src/routes/docs/approval/disclaimer/+page.svx:24,26`. Therefore, a UI-created
prize row or route that can disagree with the math book is **at risk**. The prize row,
board, route, and payout need to be generated as one consistent authoritative result.

## Frontend, rules/paytable, autoplay, and accessibility

**Frontend quality — unclear until the actual game is reviewed.**

> Frontend checks will include reviewing in-game performance and display to ensure the game is free of visual bugs, has the necessary industry-standard User Interface (UI) components, and behaves as described in the game rules.

File: `src/routes/docs/approval/frontend-requirements/+page.svx:9`.

**Rules/paytable — the base-only rules must disclose the prizes, RTP, max win, and how the feature/outlet mechanics work.**

> Game information must be accessible from the UI, including a detailed description of all game rules.

> The RTP of the game (and each mode, if applicable) must be clearly communicated to the player.

> The maximum win amount for each mode must be clearly displayed.

> Payout amounts for all symbol combinations must be presented.

> If the game includes special symbols (e.g., cash prizes or multipliers), list all obtainable values.

> For feature modes (e.g., triggered by Scatter symbols), describe how to access them. Example: "3 Scatters award 10 free spins; 4 Scatters award 15 spins ..."

File: `src/routes/docs/approval/frontend-requirements/+page.svx:20-26`. The proposed
base-only game has no scatter feature or multiplier symbols; its outlet prize values,
96.5% RTP, 50,000× Variant A cap, and dead-end behavior must still be described.

**Autoplay — conditional.**

> If an 'autoplay' feature is present, the player must confirm the autoplay action, games are not allowed to automatically place consecutive bets with one click.

File: `src/routes/docs/approval/frontend-requirements/+page.svx:37`. Not applicable
if autoplay is absent.

**Responsible gambling — not found.** No explicit responsible-gambling rule or
responsible-gambling text requirement was found in the docs repository's `src/` for
this review.

**Language and theme restrictions.**

> English is the only required language. If only English (en) is supported, on-screen text must not corrupt when other language parameters are passed.

File: `src/routes/docs/approval/rgs-requirements/+page.svx:27`.

> Stake Engine enforces a strict XSS policy. The game build must consist only of static files and cannot reach external sources. Common issues include downloading fonts from external servers, which logs console errors.

File: `src/routes/docs/approval/rgs-requirements/+page.svx:21`.

> Game assets cannot include material with Stake™ / Kick™ branding or themes.

File: `src/routes/docs/approval/+page.svx:22`. The sewer theme is **unclear** until
final assets are reviewed; keep the presentation original, age-appropriate, and
within the content restrictions above.
