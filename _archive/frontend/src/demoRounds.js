// Explicit local preview fixtures only. Production books are supplied by the RGS.
import { parseRound } from './sewerGame.js';

const patterns = [
  [
    'I0 L1 T1 X0 I2',
    'T0 X0 L2 I0 T2',
    'L1 I0 T2 W0 X1',
    'X0 T3 I0 L1 T0',
    'I1 L0 X0 T2 I0',
  ],
  [
    'I1 T0 L2 X0 I3',
    'L0 X1 T2 I0 T1',
    'T0 I1 W0 L3 X0',
    'X1 L0 T3 I2 T0',
    'I2 T1 X0 L2 I0',
  ],
  [
    'I0 L1 T2 X0 I1',
    'T0 X0 L2 I1 T2',
    'L1 I0 T2 W0 X0',
    'X0 T3 I0 L1 T0',
    'I1 L0 X0 T2 I0',
  ],
];

const entries = [
  { id: 'demo-clear-001', inlet: 2, payout: 1.5, scatters: [[0, 4], [4, 0]] },
  { id: 'demo-bonus-002', inlet: 2, payout: 12, scatters: [[0, 0], [2, 4], [4, 3]] },
  { id: 'demo-deep-003', inlet: 0, payout: 45, scatters: [[0, 4], [2, 0], [3, 3], [4, 1]] },
];

function makeRound(index) {
  const config = entries[index % entries.length];
  const board = patterns[index % patterns.length].flatMap((line) => line.split(' ').map((token) => {
    const [t, rotation] = [token[0], Number(token.slice(1))];
    return { t, r: rotation, s: false };
  }));
  for (const [row, col] of config.scatters) board[row * 5 + col] = { t: 'S', r: 0, s: true };
  // Keep every preview round solvable: move any scatter off the inlet row,
  // then author a simple eastbound path with two visible tee junctions.
  const occupiedScatters = board.map((cell, index) => cell.t === 'S' ? index : -1).filter((index) => index >= 0);
  const routeCells = Array.from({ length: 5 }, (_, col) => config.inlet * 5 + col);
  const freeCells = board.map((_, index) => index).filter((index) => !routeCells.includes(index) && board[index].t !== 'S');
  for (const index of occupiedScatters) {
    if (routeCells.includes(index)) {
      const movedTo = freeCells.shift();
      if (movedTo === undefined) throw new Error('Not enough cells to keep preview route open');
      board[movedTo] = { t: 'S', r: 0, s: true };
      board[index] = { t: 'I', r: 0, s: false };
    }
  }
  routeCells.forEach((index, col) => {
    board[index] = { t: col === 0 || col === 2 ? 'T' : 'I', r: 0, s: false };
  });
  return parseRound({
    id: config.id,
    board,
    inlet: config.inlet,
    payoutMultiplier: config.payout,
    scatterCount: config.scatters.length,
  });
}

export const demoRounds = [makeRound(0), makeRound(1), makeRound(2)];
