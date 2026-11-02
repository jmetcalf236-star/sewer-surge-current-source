# Sewer Surge — validation report

Date: 1 November 2026

## Release decision

**Not ready for provider submission.** The current source contains the game-specific Math SDK backend and Web SDK app, and local test/debug generation checks are recorded below. Production optimization, optimized LUT acceptance, exact clean SDK installation, full Web SDK production build and live RGS/provider staging remain outstanding.

## Local checks

| Check | Status | Detail |
|---|---|---|
| Math SDK contract + game tests | PASS | see log |
| Four-mode books + LUT structural audit | FAIL (1) | 4000 books; 12275 structural/LUT failures |
| Web adapter Node tests | FAIL (1) | 2 tests passed |
| Strict TypeScript adapter check | PASS | `tsc --noEmit --strict` |
| SewerSurgeWin script TypeScript check | FAIL (2) | Script block with Svelte API shims; not a Svelte compile |
| Existing standalone frontend tests | PASS | see log |
| Production shell syntax | PASS | `bash -n` |
| Python syntax | PASS | `py_compile` |

Logs and machine-readable status are included in `validation/`.

## Locked game contract

- 5×5 board; pipes `I`, `L`, `T`, `X`, `W`; scatter `S`.
- Base 1×; Ante 3×; Normal Bonus Buy 100×; Super Bonus Buy 500×.
- RTP target: 96.5% per mode; maximum win: 10,000×.
- 0–2 scatters = none; exactly 3 = Bonus; 4–5 = Deep Run.
- Ante optimizer target: 5× combined Bonus + Deep Run frequency versus Base.
- Provider display name: `KingWin`; provider number and accepted game ID remain portal-issued placeholders.

The Math SDK/RGS book is authoritative for board, rotations, inlet, scatter tier and payout. Player branch choices are local visual state only and are never serialized into the outcome or sent to the math layer.

## Four-mode debug generation

The latest smoke run generated 1,000 uncompressed debug books per mode. The independent audit checks 5×5 board size, symbols and rotations, unrotated wild/scatter, scatter count/tier, inlet, eastward route with a genuinely connected second branch, visual-only route authority, absence of player route-choice fields, custom award/SDK total/final win equality, payout increments, 10,000× cap and wincap consistency.

| Mode | Books | Raw unoptimized sample RTP | Unique payouts | LUT status | Weighted LUT RTP | Weighted hit rate | Expected 10,000× frequency (rounds) | Structural/LUT failures |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| base | 1000 | 124020.0% | 12 | unoptimized | 128882.0% | 65.0% | 1000.0 | 2204 |
| ante | 1000 | 43273.333333% | 13 | unoptimized | 46589.333333% | 70.1% | 1000.0 | 2404 |
| bonus | 1000 | 11957.5% | 13 | unoptimized | 11957.5% | 96.4% | 1.672 | 3721 |
| super_bonus | 1000 | 9935.0% | 13 | unoptimized | 9935.0% | 96.8% | 1.064 | 3946 |

The current LUTs are unoptimized; raw sample RTP and unoptimized weighted LUT RTP are not release RTP. The audit reports unique payout diversity, weighted non-zero hit rate and expected max-win frequency, with statistical warnings separate from structural failures. The production gate requires optimized LUTs for all modes, RTP within 96.5% ±0.5 percentage points, and Ante/Base combined feature-frequency ratio within 10% relative tolerance of 5×. Current optimized math audit pass: `False`.

## SDK pins and compatibility

- Math SDK source target: `engineio/math-sdk` commit `6e0c69e3a4edc80ca7e59921e31167cb2ca83c59`.
- Runtime dependency target: `StakeEngine/math-sdk` commit `0842bb244cb8c15e63af541054710a8082901e2f`.
- `SDK_PIN.txt` and `check_sdk_contract.py --require-exact-pin` enforce both commits before production generation.
- Local smoke tests/books used an extracted SDK snapshot without `.git` metadata; exact clean pinned installation is not yet verified.
- Local Web SDK snapshot has no `.git` metadata; its upstream commit is not proven (`WEB_SDK_VERSION.txt`).

## Web SDK integration

`web-sdk-integration/apps/sewer-surge/` contains the game-specific app folder: custom pipe board, connected branch chooser, authoritative event adapter, custom event preservation across resume snapshots, Sewer Surge-specific win overlay and an in-game rules panel. The rules panel explains symbols, scatter tiers, all four bet prices, max win and visual-only branch selection. It labels 96.5% as a configured target pending final verification.

The full Web SDK/Vite production build is not verified because Vite dependencies are unavailable in this workspace. Template/sample audio/static assets remain and must be replaced with original Sewer Surge assets. Mobile, popout and CDN checks are outstanding.

## Production workflow protections

Windows PowerShell and Linux/macOS scripts check Python, Rust/Cargo, `zstandard==0.23.0` and exact Math SDK source/runtime commits before generation. They then run SDK book generation, optimizer, config generation, the official SDK verifier and the independent compressed-book/weighted-LUT audit. Rust/Cargo and pinned compression dependencies were unavailable here, so this production workflow has not been run.

## Outstanding release gates

1. Run the strict setup in a clean Math SDK checkout and pass exact source/runtime commit checks.
2. Install Rust/Cargo and pinned Python dependencies; generate compressed production books.
3. Run optimization and validate weighted RTP, volatility, hit rate, max-win frequency and the 5× Ante feature target.
4. Run the official SDK RGS verifier against optimized outputs.
5. Install the app into a clean pinned Web SDK monorepo and pass the full production build.
6. Replace sample audio/assets and verify original artwork/audio, CDN, mobile and popout behaviour.
7. Obtain portal-issued KingWin provider number/game ID and complete live RGS auth, play, end-round, resume, replay and four-mode staging tests.

GitHub read access to `jmetcalf236-star/pipes` is available, but branch writes returned HTTP 403; no code has been committed there.
