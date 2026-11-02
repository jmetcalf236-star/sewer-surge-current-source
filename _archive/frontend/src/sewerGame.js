// Sewer Surge presentation rules. Routing is a visual layer only: no function
// in this module computes, modifies, or requests a payout.
export const COLS = 5;
export const ROWS = 5;
export const MAX_WIN = 10_000;
export const SIDES = ['N', 'E', 'S', 'W'];
const OPP = { N: 'S', E: 'W', S: 'N', W: 'E' };
const STEP = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
const BASE = {
  I: ['E', 'W'],
  L: ['S', 'E'],
  T: ['E', 'W', 'S'],
  X: SIDES,
  W: SIDES, // universal, unrotated connector
  S: [], // scatter tile; not a pipe
};

export function openings(piece) {
  const base = BASE[piece?.t];
  if (!base) throw new Error(`Unknown pipe piece: ${piece?.t}`);
  return base.map((d) => SIDES[(SIDES.indexOf(d) + (piece.r ?? 0)) % 4]);
}

export function getScatterTier(n) {
  if (!Number.isInteger(n) || n < 0) throw new Error('Scatter count must be a non-negative integer');
  return n >= 4 ? 'deep-run' : n === 3 ? 'bonus' : 'none';
}

export function hasEastboundRoute(board, inlet) {
  if (!Array.isArray(board) || board.length !== ROWS * COLS || !Number.isInteger(inlet)) return false;
  const queue = [{ x: 0, y: inlet, from: 'W' }];
  const seen = new Set();
  while (queue.length) {
    const { x, y, from } = queue.shift();
    const index = y * COLS + x;
    const state = `${index}:${from}`;
    if (seen.has(state)) continue;
    seen.add(state);
    const ports = openings(board[index]);
    if (!ports.includes(from)) continue;
    for (const direction of ports.filter((side) => side !== from)) {
      if (direction === 'E' && x === COLS - 1) return true;
      const [dx, dy] = STEP[direction];
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || nx >= COLS || ny < 0 || ny >= ROWS) continue;
      if (openings(board[ny * COLS + nx]).includes(OPP[direction])) {
        queue.push({ x: nx, y: ny, from: OPP[direction] });
      }
    }
  }
  return false;
}

export function validateRound(round) {
  if (!round || typeof round !== 'object') throw new Error('Malformed round: object');
  if (!Array.isArray(round.board) || round.board.length !== COLS * ROWS) throw new Error('Malformed round: board');
  let scatters = 0;
  round.board.forEach((piece) => {
    if (!piece || !Object.hasOwn(BASE, piece.t)) throw new Error('Malformed round: symbol');
    if (!Number.isInteger(piece.r) || piece.r < 0 || piece.r > 3) throw new Error('Malformed round: rotation');
    if ((piece.t === 'W' || piece.t === 'S') && piece.r !== 0) throw new Error('Malformed round: non-rotatable symbol');
    if (piece.s !== undefined && typeof piece.s !== 'boolean') throw new Error('Malformed round: scatter flag');
    const isScatter = piece.t === 'S' || piece.s === true;
    if (isScatter !== (piece.t === 'S')) throw new Error('Malformed round: scatter flag mismatch');
    scatters += Number(isScatter);
  });
  if (!Number.isInteger(round.inlet) || round.inlet < 0 || round.inlet >= ROWS) throw new Error('Malformed round: inlet');
  if (round.board[round.inlet * COLS].t === 'S') throw new Error('Malformed round: inlet starts on scatter');
  if (!openings(round.board[round.inlet * COLS]).includes('W')) throw new Error('Malformed round: inlet pipe has no west-facing port');
  if (!hasEastboundRoute(round.board, round.inlet)) throw new Error('Malformed round: no connected route to east outlet');
  if (!Number.isFinite(round.payoutMultiplier) || round.payoutMultiplier < 0 || round.payoutMultiplier > MAX_WIN) {
    throw new Error('Malformed round: payout');
  }
  if (Math.round(round.payoutMultiplier * 10) !== round.payoutMultiplier * 10) {
    throw new Error('Malformed round: payout increment');
  }
  if (round.scatterCount !== undefined && round.scatterCount !== scatters) throw new Error('Malformed round: scatter count mismatch');
  const tier = getScatterTier(scatters);
  if (round.scatterTier !== undefined && round.scatterTier !== tier) throw new Error('Malformed round: scatter tier mismatch');
  if (round.routeAuthority !== undefined && round.routeAuthority !== 'visual-only') throw new Error('Malformed round: route authority');
  return {
    id: String(round.id ?? ''),
    board: round.board.map((piece) => ({ t: piece.t, r: piece.r, s: piece.t === 'S' })),
    inlet: round.inlet,
    payoutMultiplier: round.payoutMultiplier,
    scatters,
    tier,
  };
}

export function parseRound(book) {
  return validateRound(book);
}

// Rotate a pipe locally for the water puzzle. This helper intentionally copies
// only board presentation state and never writes to payoutMultiplier.
export function rotatePipe(round, index) {
  if (!round || !Array.isArray(round.board) || !Number.isInteger(index) || index < 0 || index >= round.board.length) {
    throw new Error('Cannot rotate malformed pipe selection');
  }
  const piece = round.board[index];
  if (piece.t === 'W' || piece.t === 'S') return round;
  const board = round.board.map((cell, cellIndex) =>
    cellIndex === index ? { ...cell, r: (cell.r + 1) % 4 } : cell,
  );
  return { ...round, board };
}

function canGo(board, x, y, direction) {
  if (direction === 'E' && x === COLS - 1) return true;
  const nx = x + STEP[direction][0];
  const ny = y + STEP[direction][1];
  if (nx < 0 || nx >= COLS || ny < 0 || ny >= ROWS) return false;
  return openings(board[ny * COLS + nx]).includes(OPP[direction]);
}

// Water path is a client-side presentation. `picks` contains visual branch choices only.
export function traceFlow(board, inlet, picks = []) {
  const walk = (x, y, from, seen, branchDepth) => {
    const index = y * COLS + x;
    const key = `${index}:${from}`;
    if (seen.has(key)) return { path: [index], junctions: [], end: 'dead' };
    const nextSeen = new Set(seen);
    nextSeen.add(key);
    const exits = openings(board[index]).filter((direction) => direction !== from && canGo(board, x, y, direction));
    if (!exits.length) return { path: [index], junctions: [], end: 'dead' };

    const isJunction = exits.length > 1;
    const selected = isJunction ? picks[branchDepth] : undefined;
    const optionOrder = isJunction
      ? selected === undefined
        ? exits.map((_, i) => i)
        : Number.isInteger(selected) && selected >= 0 && selected < exits.length ? [selected] : []
      : [0];
    let firstDead = null;

    for (const optionIndex of optionOrder) {
      const direction = exits[optionIndex];
      const [dx, dy] = STEP[direction];
      const currentJunctions = isJunction ? [{ at: index, options: exits, chosen: optionIndex }] : [];
      if (direction === 'E' && x === COLS - 1) {
        return { path: [index], junctions: currentJunctions, end: 'exit' };
      }
      const child = walk(x + dx, y + dy, OPP[direction], nextSeen, branchDepth + Number(isJunction));
      const result = {
        path: [index, ...child.path],
        junctions: [...currentJunctions, ...child.junctions],
        end: child.end,
      };
      if (child.end === 'exit') return result;
      if (!firstDead) firstDead = result;
    }
    return firstDead ?? { path: [index], junctions: [], end: 'dead' };
  };

  if (!openings(board[inlet * COLS]).includes('W')) return { path: [], junctions: [], end: 'dead' };
  return walk(0, inlet, 'W', new Set(), 0);
}

// LOCAL PREVIEW ONLY. Live play must pass an official Stake Engine book through rgsAdapter.js.
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mockBook(seed) {
  const random = rng(seed);
  const types = ['I', 'I', 'L', 'L', 'L', 'T', 'T', 'X', 'W'];
  const board = Array.from({ length: COLS * ROWS }, () => ({
    t: types[Math.floor(random() * types.length)],
    r: 0,
    s: false,
  }));
  const inlet = Math.floor(random() * ROWS);
  // Deterministic demo board: a solvable eastbound route with two branchable
  // tees. These fixtures are not used for live outcomes.
  const routeCells = Array.from({ length: COLS }, (_, col) => inlet * COLS + col);
  routeCells.forEach((index, col) => {
    board[index] = { t: col === 0 || col === 2 ? 'T' : 'I', r: 0, s: false };
  });
  const scatterCount = [0, 1, 2, 3, 4][Math.floor(random() * 5)];
  const available = board.map((_, index) => index).filter((index) => !routeCells.includes(index));
  for (let i = 0; i < scatterCount; i++) {
    const chosen = Math.floor(random() * available.length);
    const index = available.splice(chosen, 1)[0];
    board[index] = { t: 'S', r: 0, s: true };
  }
  const payoutChoices = [0, 0, 0.2, 0.5, 1, 1.5, 2, 5, 8, 12, 25, 50];
  return {
    id: `preview-${seed}`,
    board,
    inlet,
    payoutMultiplier: payoutChoices[Math.floor(random() * payoutChoices.length)],
    scatterCount,
    scatterTier: getScatterTier(scatterCount),
    routeAuthority: 'visual-only',
  };
}
