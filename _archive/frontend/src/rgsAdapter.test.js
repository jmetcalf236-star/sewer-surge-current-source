import test from 'node:test';
import assert from 'node:assert/strict';
import { adaptStakeEngineEvents } from './rgsAdapter.js';

const board = Array.from({ length: 5 }, (_, row) => Array.from({ length: 5 }, (_, col) => ({
  t: row === 0 && col === 0 ? 'L' : row === 1 && col === 0 ? 'L' : 'I',
  r: row === 0 && col === 0 ? 1 : row === 1 && col === 0 ? 3 : 0,
  s: false,
})));

const makeEvents = (cents = 1250) => [
  { index: 0, type: 'reveal', board: [], paddingPositions: [], gameType: 'basegame', anticipation: [] },
  { index: 0.5, type: 'sewerBoard', board, inlet: 0, scatterCount: 0, scatterTier: 'none', waterEntry: 'west', waterExit: 'east', routeAuthority: 'visual-only', schemaVersion: 1 },
  { index: 2, type: 'sewerAward', amount: cents, payoutMultiplier: cents, scatterTier: 'none' },
  { index: 3, type: 'setWin', amount: cents, winLevel: 4 },
  { index: 4, type: 'setTotalWin', amount: cents },
  { index: 5, type: 'finalWin', amount: cents },
];

test('RGS adapter converts SDK integer-cent payout to multiplier', () => {
  const round = adaptStakeEngineEvents(makeEvents(1250), 'round-125');
  assert.equal(round.id, 'round-125');
  assert.equal(round.payoutMultiplier, 12.5);
  assert.equal(round.board.length, 25);
  assert.equal(round.inlet, 0);
});

test('RGS adapter rejects payout disagreement between award and final event', () => {
  const events = makeEvents(1250);
  events[5] = { ...events[5], amount: 1200 };
  assert.throws(() => adaptStakeEngineEvents(events), /does not match/);
});

test('RGS adapter rejects a server board whose inlet pipe has no west opening', () => {
  const events = makeEvents(1250);
  events[1] = { ...events[1], board: events[1].board.map((row) => row.map((cell) => ({ ...cell }))) };
  events[1].board[0][0] = { t: 'L', r: 0, s: false };
  assert.throws(() => adaptStakeEngineEvents(events), /west-facing port/);
});
