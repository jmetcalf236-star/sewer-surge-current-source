/**
 * Sewer Surge bridge for Stake Engine Web SDK custom book events.
 *
 * Book monetary values are SDK integer cents (100 = 1.00x). This module only
 * reads and validates the server-authored book. It never creates a bet, changes
 * an award, or accepts a route choice as payout input.
 */

export type SewerPipeType = 'I' | 'L' | 'T' | 'X' | 'W' | 'S';
export type SewerScatterTier = 'none' | 'bonus' | 'deep-run';

export type SewerPipeCell = {
  t: SewerPipeType;
  r: 0 | 1 | 2 | 3;
  s: boolean;
};

export type SewerSurgeRound = {
  id: string;
  board: SewerPipeCell[]; // flattened row-major 5x5 view-model
  inlet: number;
  payoutMultiplier: number;
  scatterCount: number;
  scatterTier: SewerScatterTier;
  routeAuthority: 'visual-only';
};

export type SewerBoardBookEvent = {
  index: number;
  type: 'sewerBoard';
  board: SewerPipeCell[][]; // row-major [row][column]
  inlet: number;
  scatterCount: number;
  scatterTier: SewerScatterTier;
  waterEntry: 'west';
  waterExit: 'east';
  routeAuthority: 'visual-only';
  schemaVersion: 1;
};

export type SewerFeatureBookEvent = {
  index: number;
  type: 'sewerFeature';
  feature: Exclude<SewerScatterTier, 'none'>;
  scatterCount: number;
  routeAuthority: 'visual-only';
};

export type SewerAwardBookEvent = {
  index: number;
  type: 'sewerAward';
  amount: number;
  payoutMultiplier: number;
  scatterTier: SewerScatterTier;
  maxWinCapped: boolean;
};

export type SewerSurgeBookEvent =
  | SewerBoardBookEvent
  | SewerFeatureBookEvent
  | SewerAwardBookEvent;

type StakeBookEvent = { index: number; type: string; amount?: number };
type StakeBook = {
  id: string | number;
  payoutMultiplier: number;
  events: StakeBookEvent[];
};

const MAX_WIN_X = 10_000;
const MAX_WIN_CENTS = MAX_WIN_X * 100;

function tierForScatterCount(count: number): SewerScatterTier {
  return count >= 4 ? 'deep-run' : count === 3 ? 'bonus' : 'none';
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`Invalid Sewer Surge book: ${message}`);
}

function toRound(
  events: StakeBookEvent[],
  id: string,
  bookPayoutCents?: number,
): SewerSurgeRound {
  const boardEvent = events.find((event) => event.type === 'sewerBoard') as
    | SewerBoardBookEvent
    | undefined;
  const awardEvent = events.find((event) => event.type === 'sewerAward') as
    | SewerAwardBookEvent
    | undefined;
  const finalWinEvent = [...events].reverse().find((event) => event.type === 'finalWin');

  assert(boardEvent, 'missing sewerBoard event');
  assert(awardEvent, 'missing sewerAward event');
  assert(boardEvent.schemaVersion === 1, 'unsupported board schema version');
  assert(boardEvent.waterEntry === 'west' && boardEvent.waterExit === 'east', 'invalid water direction');
  assert(boardEvent.routeAuthority === 'visual-only', 'route selection must remain visual-only');
  assert(Array.isArray(boardEvent.board) && boardEvent.board.length === 5, 'board must have five rows');
  assert(boardEvent.board.every((row) => Array.isArray(row) && row.length === 5), 'board must be 5x5');

  const flat = boardEvent.board.flat();
  let scatterCount = 0;
  for (const cell of flat) {
    assert(cell && ['I', 'L', 'T', 'X', 'W', 'S'].includes(cell.t), 'unknown pipe symbol');
    assert(Number.isInteger(cell.r) && cell.r >= 0 && cell.r <= 3, 'invalid rotation');
    assert((cell.t !== 'W' && cell.t !== 'S') || cell.r === 0, 'wild/scatter must not rotate');
    assert(cell.s === (cell.t === 'S'), 'scatter flag does not match symbol');
    scatterCount += Number(cell.t === 'S');
  }

  assert(Number.isInteger(boardEvent.inlet) && boardEvent.inlet >= 0 && boardEvent.inlet < 5, 'inlet must be row 0–4');
  const inletCell = boardEvent.board[boardEvent.inlet][0];
  assert(inletCell.t !== 'S', 'inlet cannot start on a scatter');
  const baseOpenings: Record<SewerPipeType, readonly string[]> = {
    I: ['E', 'W'], L: ['S', 'E'], T: ['E', 'W', 'S'],
    X: ['N', 'E', 'S', 'W'], W: ['N', 'E', 'S', 'W'], S: [],
  };
  const directions = ['N', 'E', 'S', 'W'];
  const westPorts = baseOpenings[inletCell.t].map((side) => directions[(directions.indexOf(side) + inletCell.r) % 4]);
  assert(westPorts.includes('W'), 'inlet pipe must expose a west-facing port');
  const opposite: Record<string, string> = { N: 'S', E: 'W', S: 'N', W: 'E' };
  const step: Record<string, [number, number]> = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
  const queue: Array<{ row: number; col: number; entry: string }> = [{ row: boardEvent.inlet, col: 0, entry: 'W' }];
  const seen = new Set<string>();
  let reachesOutlet = false;
  while (queue.length && !reachesOutlet) {
    const current = queue.shift()!;
    const key = `${current.row}:${current.col}:${current.entry}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const cell = boardEvent.board[current.row][current.col];
    const ports = baseOpenings[cell.t].map((side) => directions[(directions.indexOf(side) + cell.r) % 4]);
    if (!ports.includes(current.entry)) continue;
    for (const exit of ports.filter((side) => side !== current.entry)) {
      if (exit === 'E' && current.col === 4) { reachesOutlet = true; break; }
      const [dx, dy] = step[exit];
      const nextCol = current.col + dx;
      const nextRow = current.row + dy;
      if (nextCol < 0 || nextCol >= 5 || nextRow < 0 || nextRow >= 5) continue;
      const neighbour = boardEvent.board[nextRow][nextCol];
      const neighbourPorts = baseOpenings[neighbour.t].map((side) => directions[(directions.indexOf(side) + neighbour.r) % 4]);
      if (neighbourPorts.includes(opposite[exit])) queue.push({ row: nextRow, col: nextCol, entry: opposite[exit] });
    }
  }
  assert(reachesOutlet, 'initial pipe rotations do not connect west inlet to east outlet');
  assert(scatterCount === boardEvent.scatterCount, 'scatter count does not match board');
  assert(tierForScatterCount(scatterCount) === boardEvent.scatterTier, 'scatter tier does not match board');
  assert(
    scatterCount === 3 ? events.some((event) => event.type === 'sewerFeature' && (event as SewerFeatureBookEvent).feature === 'bonus') :
    scatterCount >= 4 ? events.some((event) => event.type === 'sewerFeature' && (event as SewerFeatureBookEvent).feature === 'deep-run') :
    !events.some((event) => event.type === 'sewerFeature'),
    'feature event does not match scatter rules',
  );

  const authoritativeCents = Number(bookPayoutCents ?? finalWinEvent?.amount ?? awardEvent.payoutMultiplier);
  assert(Number.isInteger(authoritativeCents) && authoritativeCents >= 0, 'invalid payout encoding');
  assert(authoritativeCents <= MAX_WIN_CENTS, 'payout exceeds 10,000x max win');
  assert(authoritativeCents % 10 === 0, 'payout must use 0.1x increments');
  assert(awardEvent.amount === authoritativeCents, 'sewerAward.amount differs from authoritative payout');
  assert(awardEvent.payoutMultiplier === authoritativeCents, 'sewerAward.payoutMultiplier differs from authoritative payout');
  assert(awardEvent.scatterTier === boardEvent.scatterTier, 'award tier differs from board tier');
  if (finalWinEvent?.amount !== undefined) {
    assert(finalWinEvent.amount === authoritativeCents, 'finalWin differs from authoritative payout');
  }

  return {
    id,
    board: flat,
    inlet: boardEvent.inlet,
    payoutMultiplier: authoritativeCents / 100,
    scatterCount,
    scatterTier: boardEvent.scatterTier,
    routeAuthority: 'visual-only',
  };
}

export function adaptSewerSurgeBook(book: StakeBook): SewerSurgeRound {
  assert(book && Array.isArray(book.events), 'book.events must be an array');
  return toRound(book.events, String(book.id), book.payoutMultiplier);
}

export function adaptSewerSurgeBookEvents(events: StakeBookEvent[], id = 'rgs-round'): SewerSurgeRound {
  assert(Array.isArray(events), 'book events must be an array');
  return toRound(events, id);
}

export function publishSewerSurgeBook(book: StakeBook, target: Window = window): SewerSurgeRound {
  const round = adaptSewerSurgeBook(book);
  target.dispatchEvent(new CustomEvent<SewerSurgeRound>('sewer-surge:book', { detail: round }));
  return round;
}

export function publishSewerSurgeBookEvents(
  events: StakeBookEvent[],
  id = 'rgs-round',
  target: Window = window,
): SewerSurgeRound {
  const round = adaptSewerSurgeBookEvents(events, id);
  target.dispatchEvent(new CustomEvent<SewerSurgeRound>('sewer-surge:book', { detail: round }));
  return round;
}
