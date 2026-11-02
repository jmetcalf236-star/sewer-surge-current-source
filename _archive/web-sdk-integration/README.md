# Sewer Surge — Web SDK game app

`apps/sewer-surge/` contains the complete game-specific app folder to place inside the
official `engineio/web-sdk` monorepo. It is not a replacement for the Web SDK monorepo or
its shared workspace packages.

## What is integrated

- Svelte game app using the standard Stake Web SDK `App`, `UI`, authentication, betting
  actor and round lifecycle.
- Game-specific 5×5 pipe board in `src/components/SewerSurgeBoard.svelte`.
- Sewer Surge event types and handlers for `sewerBoard`, `sewerFeature` and `sewerAward`.
- Strict adapter validation: 5×5 board, valid symbols/rotations, fixed wild/scatter,
  west-to-east route, a genuinely connected branch on the route, scatter-tier mapping,
  `setTotalWin`/`finalWin`/`wincap` consistency and no player route choices in the book.
- Local-only branch selection. It changes the illuminated route only; it is never
  submitted to the Math SDK/RGS and cannot change the selected outcome or payout.
- A default visual route that passes through a real branch point, with reduced-motion
  support for the water-flow animation.
- Sewer Surge-specific win overlay in `SewerSurgeWin.svelte` rather than the template's
  sample win animation.
- Resume handling that preserves Sewer Surge board/feature/award/wincap/finalWin events
  inside the Web SDK resume snapshot and reconstructs the board/award after a disconnect.

## Local checks

From `apps/sewer-surge/`:

```bash
node --experimental-strip-types --test tests/sewerSurgeAdapter.test.mjs

tsc --noEmit --strict --target ES2022 --module ESNext --moduleResolution bundler   src/game/sewerSurgeAdapter.ts src/game/sewerSurgeTypes.ts
```

These checks cover the adapter and its event validation. They do not replace a full
workspace install/build or a live RGS session.

## Remaining frontend release work

1. Install this app in a clean checkout of the exact Web SDK commit recorded for the
   submission, install the monorepo's pinned Node/pnpm dependencies, and run the complete
   production build.
2. Replace the remaining template/sample sound assets with original Sewer Surge audio.
   The board and win overlay are game-specific, but the current app still inherits sample
   audio/static assets from the SDK template.
3. Verify all visual assets and fonts are hosted through the Stake Engine CDN after
   upload; check mobile and popout layouts.
4. Test live RGS authentication, play, end-round, disconnect/resume, bet replay and all
   four bet modes in the provider's staging environment.
5. Replace the development game ID with the accepted KingWin/Stake portal game ID.

The local Vite production build was attempted but could not run because this workspace
has no installed Vite dependencies. No live RGS/staging test has been performed. The app
is an integrated development candidate, not an RGS-certified frontend release.

## Clean Web SDK workspace setup

The official Web SDK workspace uses Node 22.16.0 and pnpm 10.5.0 in the upstream setup notes. In a clean checkout of `https://github.com/engineio/web-sdk`:

```bash
pnpm install --frozen-lockfile
```

Copy this package's `apps/sewer-surge/` folder into the monorepo's `apps/` directory, apply the event type additions documented in `patches/` if the target SDK revision does not already contain them, then run the build/check scripts declared by `apps/sewer-surge/package.json` from the monorepo root. Record the exact Web SDK commit in `WEB_SDK_VERSION.txt` before treating that workspace as pinned.
