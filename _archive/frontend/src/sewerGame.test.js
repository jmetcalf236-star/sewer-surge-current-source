import test from 'node:test';
import assert from 'node:assert/strict';
import { COLS, ROWS, openings, traceFlow, getScatterTier, parseRound, mockBook, validateRound, hasEastboundRoute, rotatePipe } from './sewerGame.js';

const row = (types) => types.map((t) => ({ t, r: 0 }));
const empty = () => Array.from({ length: COLS * ROWS }, () => ({ t: 'L', r: 0 }));

test('rotation turns openings clockwise', () => {
  assert.deepEqual(openings({ t: 'L', r: 0 }).sort(), ['E', 'S']);
  assert.deepEqual(openings({ t: 'L', r: 1 }).sort(), ['S', 'W']);
  assert.throws(() => openings({ t: 'Z' }));
});

test('straight row reaches the outlet', () => {
  const board = empty();
  board.splice(2 * COLS, COLS, ...row(['I', 'I', 'I', 'I', 'I']));
  const f = traceFlow(board, 2);
  assert.equal(f.end, 'exit');
  assert.deepEqual(f.path, [10, 11, 12, 13, 14]);
});

test('eastbound route validator detects an impossible board', () => {
  const board = empty();
  board.splice(2 * COLS, COLS, ...row(['I', 'I', 'L', 'I', 'I']));
  assert.equal(hasEastboundRoute(board, 2), false);
});

test('dead end when the next pipe does not connect', () => {
  const board = empty();
  board.splice(0, COLS, ...row(['I', 'I', 'L', 'I', 'I']));
  assert.equal(traceFlow(board, 0).end, 'dead');
});

test('inlet tile must accept water from the west', () => {
  const board = empty();
  assert.equal(traceFlow(board, 0).end, 'dead');
});

test('junction picks change the route but never the payout', () => {
  const board = empty();
  board.splice(2 * COLS, COLS, ...row(['I', 'X', 'I', 'I', 'I']));
  board[2 * COLS + 1] = { t: 'X', r: 0 };
  board[1 * COLS + 1] = { t: 'I', r: 1 };
  const a = traceFlow(board, 2, [0]);
  const b = traceFlow(board, 2, [1]);
  assert.equal(a.junctions.length, 1);
  assert.notDeepEqual(a.path, b.path);
  const book = { id: 'x', board, inlet: 2, payoutMultiplier: 7 };
  assert.equal(parseRound(book).payoutMultiplier, 7);
  assert.equal(parseRound({ ...book }).payoutMultiplier, 7);
});

test('scatter thresholds 0-2, 3, 4, 5+', () => {
  assert.deepEqual([0, 1, 2, 3, 4, 5, 6].map(getScatterTier), ['none', 'none', 'none', 'bonus', 'deep-run', 'deep-run', 'deep-run']);
});

test('malformed rounds are rejected', () => {
  const ok = mockBook(1);
  assert.doesNotThrow(() => parseRound(ok));
  assert.throws(() => parseRound(null));
  assert.throws(() => parseRound({ ...ok, board: ok.board.slice(1) }));
  assert.throws(() => parseRound({ ...ok, inlet: 9 }));
  assert.throws(() => parseRound({ ...ok, payoutMultiplier: -1 }));
  assert.throws(() => parseRound({ ...ok, board: ok.board.map(() => null) }));
});

test('local pipe rotation and branch choices never change fixed payout', () => {
  const round = parseRound(mockBook(83));
  const rotated = rotatePipe(round, round.inlet * COLS + 1);
  assert.equal(rotated.payoutMultiplier, round.payoutMultiplier);
  assert.notEqual(rotated.board[round.inlet * COLS + 1].r, round.board[round.inlet * COLS + 1].r);
  assert.equal(rotatePipe(round, round.inlet * COLS).payoutMultiplier, round.payoutMultiplier);
  const before = round.payoutMultiplier;
  traceFlow(round.board, round.inlet, [1, 0, 1]);
  assert.equal(round.payoutMultiplier, before);
});

test('same seed gives the same round (replay)', () => {
  assert.deepEqual(mockBook(42), mockBook(42));
  const r = parseRound(mockBook(42));
  assert.deepEqual(traceFlow(r.board, r.inlet), traceFlow(r.board, r.inlet));
});


test('rejects an inlet tile that does not expose its west port', () => {
  const round = mockBook(2026);
  round.board[round.inlet * 5] = { t: 'L', r: 0, s: false };
  assert.throws(() => validateRound(round), /west-facing port/);
});
