SEWER SURGE — Game-specific Math SDK notes

Board
- The outcome board is 5 columns by 5 rows.
- Pipe symbols: I (straight), L (elbow), T (tee), X (cross), W (wild connector).
- Scatter symbol: S.
- Every pipe except W may rotate. W is fixed at rotation 0; S is not a pipe and is also fixed.
- Water enters through the west edge at the authoritative inlet row and has a valid eastward route.
- Every accepted board has at least one real connected branch point on a west-to-east route. If a T/X/W has no second connected exit, the generator rotates an off-route neighbour to create a genuine second option.

Features
- 0, 1 or 2 scatters: no feature.
- Exactly 3 scatters: Bonus.
- 4 or 5 scatters: Deep Run.
- Base bet cost: 1x.
- Ante bet cost: 3x; the optimizer targets 5x the combined Bonus + Deep Run frequency of Base.
- Normal Bonus Buy cost: 100x.
- Super Bonus Buy cost: 500x.
- Target RTP: 96.5% for each mode.
- Maximum win: 10,000x.

Outcome authority
- The Math SDK generates the board, rotations, inlet, scatter tier, payout and authoritative book events.
- Frontend branch selection changes only the locally highlighted water route. It is never sent to the Math SDK/RGS, is not included in the outcome book, and cannot alter payoutMultiplier or the selected outcome.

Identifiers
- Provider display name: KingWin.
- provider_number=0 and game_id=0_0_sewersurge are local development placeholders. Replace only with portal-issued production values.
