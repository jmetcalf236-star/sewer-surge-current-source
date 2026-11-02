# Release staging is gated, not hand-authored

`npm run prepare:upload -- <SDK-game-directory> <frontend-dist-directory>` invokes the strict `scripts/prepare-upload.mjs` release gate. It refuses to stage if the official SDK-generated compressed books/LUTs/configs/forces are missing, the KingWin provider number is still a placeholder, any mode price differs from the configured contract, any mode RTP is outside 96.5% ± 0.2 percentage points, or max-win/volatility limits fail.

The script does not generate math, optimize books, certify RTP, or contact Stake Engine. Run the pinned Math SDK generation/optimizer/verifier first, build the production Web SDK app, and obtain provider/RGS approval.

Normal Bonus is 100x as confirmed by the game owner. Super Bonus is currently configured at 500x as confirmed by the game owner.
