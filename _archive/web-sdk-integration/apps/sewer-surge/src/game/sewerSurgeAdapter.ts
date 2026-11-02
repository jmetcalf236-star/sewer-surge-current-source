import type {
  BookEventSewerAward,
  BookEventSewerBoard,
  BookEventSewerFeature,
  SewerPipeCell,
  SewerPipeType,
  SewerScatterTier,
  SewerSurgeRoundState,
} from './sewerSurgeTypes';

const MAX_WIN_CENTS = 1_000_000;
const BASE_PORTS: Record<SewerPipeType, readonly string[]> = {
  I: ['E', 'W'],
  L: ['S', 'E'],
  T: ['E', 'W', 'S'],
  X: ['N', 'E', 'S', 'W'],
  W: ['N', 'E', 'S', 'W'],
  S: [],
};
const DIRECTIONS = ['N', 'E', 'S', 'W'] as const;
const OPPOSITE: Record<string, string> = { N: 'S', E: 'W', S: 'N', W: 'E' };
const STEP: Record<string, [number, number]> = {
  N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0],
};

type EventLike = { index: number; type: string; [key: string]: unknown };

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`Invalid Sewer Surge book: ${message}`);
}

function ports(cell: SewerPipeCell): string[] {
  return BASE_PORTS[cell.t].map((side) => DIRECTIONS[(DIRECTIONS.indexOf(side as (typeof DIRECTIONS)[number]) + cell.r) % 4]);
}

function hasWestToEastRoute(board: SewerPipeCell[][], inlet: number): boolean {
  // Validate a simple eastward route that has at least one real, connected
  // branch point. Merely finding a T/X/W symbol somewhere on the board is not
  // enough; at least two outgoing neighbours must actually connect.
  const visited = new Set<string>();
  const search = (row: number, col: number, entry: string, hasBranch: boolean): boolean => {
    const key = `${row}:${col}`;
    if (visited.has(key)) return false;
    const currentPorts = ports(board[row][col]);
    if (!currentPorts.includes(entry)) return false;
    visited.add(key);

    const outgoing: string[] = [];
    for (const side of currentPorts) {
      if (side === entry || side === 'W') continue;
      if (side === 'E' && col === 4) {
        outgoing.push(side);
        continue;
      }
      const [dx, dy] = STEP[side];
      const nextCol = col + dx;
      const nextRow = row + dy;
      if (nextRow >= 0 && nextRow < 5 && nextCol >= 0 && nextCol < 5 && ports(board[nextRow][nextCol]).includes(OPPOSITE[side])) {
        outgoing.push(side);
      }
    }

    const branchExists = hasBranch || outgoing.length > 1;
    for (const side of outgoing) {
      if (side === 'E' && col === 4) {
        if (branchExists) return true;
        continue;
      }
      const [dx, dy] = STEP[side];
      if (search(row + dy, col + dx, OPPOSITE[side], branchExists)) return true;
    }

    visited.delete(key);
    return false;
  };

  return search(inlet, 0, 'W', false);
}


function flattenBookEvents(events: readonly EventLike[]): EventLike[] {
  const flattened: EventLike[] = [];
  for (const event of events) {
    if (event.type === 'createBonusSnapshot' && Array.isArray(event.bookEvents)) {
      flattened.push(...flattenBookEvents(event.bookEvents as EventLike[]));
    } else {
      flattened.push(event);
    }
  }
  return flattened;
}

function tierForScatterCount(count: number): SewerScatterTier {
  return count >= 4 ? 'deep-run' : count === 3 ? 'bonus' : 'none';
}

export function validateSewerBookEvents(events: readonly EventLike[], bookId: string | number | null = null): SewerSurgeRoundState {
  const flattenedEvents = flattenBookEvents(events);
  const boardEvent = flattenedEvents.find((event) => event.type === 'sewerBoard') as BookEventSewerBoard | undefined;
  const featureEvent = flattenedEvents.find((event) => event.type === 'sewerFeature') as BookEventSewerFeature | undefined;
  const awardEvent = flattenedEvents.find((event) => event.type === 'sewerAward') as BookEventSewerAward | undefined;
  const finalWin = [...flattenedEvents].reverse().find((event) => event.type === 'finalWin') as { amount?: unknown } | undefined;
  const totalWin = [...flattenedEvents].reverse().find((event) => event.type === 'setTotalWin') as { amount?: unknown } | undefined;

  assert(boardEvent, 'missing sewerBoard event');
  assert(awardEvent, 'missing sewerAward event');
  assert(boardEvent.schemaVersion === 1, 'unsupported board schema version');
  assert(boardEvent.waterEntry === 'west' && boardEvent.waterExit === 'east', 'invalid water direction');
  assert(boardEvent.routeAuthority === 'visual-only', 'route selection must remain visual-only');
  assert(!('routeChoice' in boardEvent) && !('branchChoice' in boardEvent) && !('selectedBranches' in boardEvent), 'player route choices must not enter the authoritative book');
  assert(Array.isArray(boardEvent.board) && boardEvent.board.length === 5, 'board must have five rows');
  assert(boardEvent.board.every((row) => Array.isArray(row) && row.length === 5), 'board must be 5x5');

  let scatters = 0;
  for (const row of boardEvent.board) {
    for (const cell of row) {
      assert(cell && ['I', 'L', 'T', 'X', 'W', 'S'].includes(cell.t), 'unknown pipe type');
      assert(Number.isInteger(cell.r) && cell.r >= 0 && cell.r <= 3, 'invalid rotation');
      assert((cell.t !== 'W' && cell.t !== 'S') || cell.r === 0, 'wild/scatter cannot rotate');
      assert(typeof cell.s === 'boolean' && cell.s === (cell.t === 'S'), 'scatter flag mismatch');
      scatters += Number(cell.t === 'S');
    }
  }

  assert(Number.isInteger(boardEvent.inlet) && boardEvent.inlet >= 0 && boardEvent.inlet <= 4, 'invalid inlet row');
  const inletCell = boardEvent.board[boardEvent.inlet][0];
  assert(inletCell.t !== 'S', 'inlet cannot be a scatter');
  assert(ports(inletCell).includes('W'), 'inlet pipe must expose its west port');
  assert(hasWestToEastRoute(boardEvent.board, boardEvent.inlet), 'board lacks an eastward route with a connected branchable junction');
  assert(scatters === boardEvent.scatterCount, 'scatter count does not match board');
  assert(tierForScatterCount(scatters) === boardEvent.scatterTier, 'scatter tier does not match board');

  if (scatters === 3) {
    assert(featureEvent?.feature === 'bonus' && featureEvent.scatterCount === scatters, 'three scatters require Bonus feature event');
  } else if (scatters >= 4) {
    assert(featureEvent?.feature === 'deep-run' && featureEvent.scatterCount === scatters, 'four or more scatters require Deep Run feature event');
  } else {
    assert(!featureEvent, 'zero to two scatters must not emit a feature event');
  }
  assert(!featureEvent || featureEvent.routeAuthority === 'visual-only', 'feature route authority must be visual-only');

  const payoutCents = awardEvent.amount;
  assert(Number.isSafeInteger(payoutCents) && payoutCents >= 0 && payoutCents <= MAX_WIN_CENTS, 'award exceeds payout constraints');
  assert(awardEvent.payoutMultiplier === payoutCents, 'award amount and payoutMultiplier disagree');
  assert(awardEvent.scatterTier === boardEvent.scatterTier, 'award scatter tier does not match board');
  assert(finalWin && Number.isSafeInteger(finalWin.amount), 'missing or malformed finalWin event');
  assert(finalWin.amount === payoutCents, 'sewerAward differs from SDK finalWin');
  assert(totalWin && Number.isSafeInteger(totalWin.amount), 'missing or malformed setTotalWin event');
  assert(totalWin.amount === payoutCents, 'sewerAward differs from SDK setTotalWin');
  const wincapEvents = flattenedEvents.filter((event) => event.type === 'wincap') as Array<{ amount?: unknown }>;
  if (payoutCents === MAX_WIN_CENTS) {
    assert(wincapEvents.length === 1 && wincapEvents[0].amount === MAX_WIN_CENTS, '10,000× award must include one matching wincap event');
  } else {
    assert(wincapEvents.length === 0, 'wincap event is only valid at the maximum payout');
  }
  assert(awardEvent.maxWinCapped === (payoutCents === MAX_WIN_CENTS), 'max-win flag is inconsistent');

  return {
    board: boardEvent.board,
    inlet: boardEvent.inlet,
    scatterCount: scatters,
    scatterTier: boardEvent.scatterTier,
    payoutCents,
    maxWinCapped: awardEvent.maxWinCapped,
    bookId,
  };
}
