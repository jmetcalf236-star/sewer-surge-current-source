# Sewer Surge frontend

This is the Svelte 5 preview frontend for Sewer Surge. Its visual direction is an original underground flow-control room: dark steel panels, hazard accents, green water illumination, a 5×5 pipe chamber, pressure/inlet/outlet instrumentation, scatter status and a fixed award display.

The frontend accepts an authoritative round through `src/rgsAdapter.js` and the `sewer-surge:book` event. The `src/SewerSurgeBoard.svelte` component can be embedded in a production Web SDK app. `src/demoRounds.js` and the preview SPIN control are demonstration-only; they do not implement the RGS wager lifecycle.

## Local preview

Requires Node.js 22.16.0.

```bash
npm install
npm test
npm run dev
```

Run `npm run build` to create the static frontend in `dist/`. A clean dependency install is recommended before building.

## Production Web SDK integration

The archive root folder `../web-sdk-integration/` contains the typed `sewerBoard`, `sewerFeature`, and `sewerAward` event adapter plus patch snippets for the current public `engineio/web-sdk` event type and handler map patterns. Use those files with the official SDK's current sample app; keep its authentication, bet actor, and end-round lifecycle intact.

Branch choices only change the local water-path highlight. They must never be sent to the RGS or used to calculate a win. The Math SDK book is authoritative for `payoutMultiplier`.

## Math source

The official Math SDK game is provided at the archive root under `../math-sdk-drop-in/games/0_0_sewersurge/`. See the archive root README and `../validation/validation-report.md` for the Math SDK command and current release gates.
