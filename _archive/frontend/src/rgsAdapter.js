import { parseRound } from './sewerGame.js';

/**
 * Convert an official Math SDK book or its full book-event sequence into the
 * Sewer Surge view-model. The SDK serialises payoutMultiplier/event amounts in
 * integer cents (100 means 1.00x); the custom sewerBoard is a row-major 5x5 grid.
 */
export function adaptStakeEngineBook(book) {
  if (!book || !Array.isArray(book.events)) throw new Error('Invalid Stake Engine book');
  return adaptStakeEngineEvents(book.events, book.id, book.payoutMultiplier);
}

export function adaptStakeEngineEvents(events, id = 'rgs-round', bookPayoutCents = undefined) {
  if (!Array.isArray(events)) throw new Error('Invalid Stake Engine book events');
  const boardEvent = events.find((event) => event.type === 'sewerBoard');
  const awardEvent = events.find((event) => event.type === 'sewerAward');
  const finalWinEvent = [...events].reverse().find((event) => event.type === 'finalWin');
  if (!boardEvent || !awardEvent) throw new Error('Stake Engine book is missing sewerBoard or sewerAward');
  if (boardEvent.schemaVersion !== 1) throw new Error('Stake Engine Sewer Surge board schema version is unsupported');
  if (boardEvent.waterEntry !== 'west' || boardEvent.waterExit !== 'east') throw new Error('Stake Engine Sewer Surge water direction is invalid');
  if (boardEvent.routeAuthority !== 'visual-only') throw new Error('Stake Engine Sewer Surge route must remain visual-only');

  const authoritativeCents = Number(bookPayoutCents ?? finalWinEvent?.amount ?? awardEvent.payoutMultiplier);
  if (!Number.isInteger(authoritativeCents) || authoritativeCents < 0) {
    throw new Error('Invalid Stake Engine payoutMultiplier encoding');
  }
  for (const value of [awardEvent.payoutMultiplier, awardEvent.amount, finalWinEvent?.amount]) {
    if (value !== undefined && Number(value) !== authoritativeCents) {
      throw new Error('Stake Engine award event does not match final round payout');
    }
  }

  const board = boardEvent.board?.flat?.();
  return parseRound({
    id,
    board,
    inlet: boardEvent.inlet,
    payoutMultiplier: authoritativeCents / 100,
    scatterCount: boardEvent.scatterCount,
    scatterTier: boardEvent.scatterTier,
    routeAuthority: boardEvent.routeAuthority,
  });
}

/**
 * Bridge for an SDK bookEventHandlerMap. It does not call the RGS or place bets;
 * the official SDK actor remains responsible for those operations.
 */
export function publishStakeEngineBook(book, target = window) {
  const round = adaptStakeEngineBook(book);
  target.dispatchEvent(new CustomEvent('sewer-surge:book', { detail: round }));
  return round;
}

export function publishStakeEngineEvents(events, id = 'rgs-round', target = window) {
  const round = adaptStakeEngineEvents(events, id);
  target.dispatchEvent(new CustomEvent('sewer-surge:book', { detail: round }));
  return round;
}
