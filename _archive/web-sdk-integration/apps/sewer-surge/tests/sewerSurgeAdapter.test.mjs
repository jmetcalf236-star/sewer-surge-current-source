import test from 'node:test';
import assert from 'node:assert/strict';
import { validateSewerBookEvents } from '../src/game/sewerSurgeAdapter.ts';

function makeBoard({ connectedBranch = true } = {}) {
  const board = Array.from({ length: 5 }, () =>
    Array.from({ length: 5 }, () => ({ t: 'I', r: 0, s: false })),
  );
  // Main route is row 2, west to east.
  board[2][2] = { t: 'T', r: 0, s: false };
  if (connectedBranch) board[3][2] = { t: 'I', r: 1, s: false };
  return board;
}

function makeBook({ amount = 123, board = makeBoard(), includeWincap = false, boardPatch = {} } = {}) {
  const boardEvent = {
    index: 0,
    type: 'sewerBoard',
    board,
    inlet: 2,
    scatterCount: 0,
    scatterTier: 'none',
    waterEntry: 'west',
    waterExit: 'east',
    routeAuthority: 'visual-only',
    schemaVersion: 1,
    ...boardPatch,
  };
  const events = [
    boardEvent,
    { index: 1, type: 'sewerFeature', scatterCount: 0, scatterTier: 'none', routeAuthority: 'visual-only' },
    { index: 2, type: 'sewerAward', amount, payoutMultiplier: amount, scatterTier: 'none', maxWinCapped: amount === 1_000_000 },
    { index: 3, type: 'setTotalWin', amount },
  ];
  if (includeWincap) events.push({ index: 4, type: 'wincap', amount: 1_000_000 });
  events.push({ index: events.length, type: 'finalWin', amount });
  return events;
}

test('accepts an authoritative 5x5 book with a real connected branch', () => {
  const round = validateSewerBookEvents(makeBook());
  assert.equal(round.inlet, 2);
  assert.equal(round.payoutCents, 123);
  assert.equal(round.scatterTier, 'none');
});

test('rejects a T symbol that has no second connected exit', () => {
  assert.throws(
    () => validateSewerBookEvents(makeBook({ board: makeBoard({ connectedBranch: false }) })),
    /connected branchable junction/,
  );
});

test('rejects player route choices in the authoritative board event', () => {
  assert.throws(
    () => validateSewerBookEvents(makeBook({ boardPatch: { routeChoice: 'south' } })),
    /player route choices must not enter/,
  );
});

test('reconstructs custom events preserved inside an RGS resume snapshot', () => {
  const events = makeBook();
  const round = validateSewerBookEvents([{ index: 0, type: 'createBonusSnapshot', bookEvents: events }]);
  assert.equal(round.payoutCents, 123);
});

test('requires a matching wincap event for a 10,000x award', () => {
  assert.throws(
    () => validateSewerBookEvents(makeBook({ amount: 1_000_000 })),
    /10,000× award must include one matching wincap event/,
  );
  const round = validateSewerBookEvents(makeBook({ amount: 1_000_000, includeWincap: true }));
  assert.equal(round.maxWinCapped, true);
});
