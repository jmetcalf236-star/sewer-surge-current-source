import _ from 'lodash';

import { stateBet } from 'state-shared';
import { checkIsMultipleRevealEvents } from 'utils-book';
import { createPrimaryMachines, createIntermediateMachines, createGameActor } from 'utils-xstate';

import type { Bet } from './typesBookEvent';
import { stateXstateDerived } from './stateXstate';
import { playBet, convertTorResumableBet } from './utils';
import { stateGame } from './stateGame.svelte';
import { validateSewerBookEvents } from './sewerSurgeAdapter';

const primaryMachines = createPrimaryMachines<Bet>({
	onResumeGameActive: (betToResume) => {
		const sewerBoardEvent = _.findLast(betToResume.state, (event) => event?.type === 'sewerBoard');
		stateGame.sewerBoardEvent = (sewerBoardEvent as typeof stateGame.sewerBoardEvent) ?? null;
		stateGame.sewerMaxWinReached = betToResume.state.some((event) => event?.type === 'wincap');
		try {
			stateGame.sewerRound = validateSewerBookEvents(
				betToResume.state as unknown as Array<{ index: number; type: string; [key: string]: unknown }>,
			);
		} catch {
			stateGame.sewerRound = null;
		}
		return convertTorResumableBet(betToResume);
	},
	onResumeGameInactive: (betToResume) => {
		stateGame.sewerBoardEvent = null;
		stateGame.sewerRound = null;
		stateGame.sewerMaxWinReached = false;
		const sewerBoardEvent = _.findLast(betToResume.state, (event) => event?.type === 'sewerBoard');
		if (sewerBoardEvent) stateGame.sewerBoardEvent = sewerBoardEvent as typeof stateGame.sewerBoardEvent;
		stateGame.sewerMaxWinReached = betToResume.state.some((event) => event?.type === 'wincap');
		try {
			stateGame.sewerRound = validateSewerBookEvents(
				betToResume.state as unknown as Array<{ index: number; type: string; [key: string]: unknown }>,
			);
		} catch {
			// An interrupted/incomplete round is replayed by the normal actor path.
			stateGame.sewerRound = null;
		}
	},
	onNewGameStart: async () => {
		stateGame.sewerBoardEvent = null;
		stateGame.sewerRound = null;
		stateGame.sewerMaxWinReached = false;
		if ((stateBet.isTurbo && stateXstateDerived.isAutoBetting()) || stateBet.isSpaceHold) return;
		stateBet.winBookEventAmount = 0;
	},
	onNewGameError: () => {
		stateGame.sewerBoardEvent = null;
		stateGame.sewerRound = null;
	},
	onPlayGame: async (bet) => await playBet(bet),
	checkIsBonusGame: (bet) => checkIsMultipleRevealEvents({ bookEvents: bet.state }),
});

const intermediateMachines = createIntermediateMachines(primaryMachines);

export const gameActor = createGameActor(intermediateMachines);
