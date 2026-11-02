<script lang="ts">
	import { onMount } from 'svelte';
	import { EnablePixiExtension } from 'components-pixi';
	import { EnableHotkey } from 'components-shared';
	import { App, Text, REM } from 'pixi-svelte';
	import { stateModal } from 'state-shared';
	import { UI, UiGameName } from 'components-ui-pixi';
	import { GameVersion, Modals } from 'components-ui-html';
	import { getContext } from '../game/context';
	import EnableSound from './EnableSound.svelte';
	import EnableGameActor from './EnableGameActor.svelte';
	import ResumeBet from './ResumeBet.svelte';
	import SewerSurgeWin from './SewerSurgeWin.svelte';
	import LoadingScreen from './LoadingScreen.svelte';
	import SewerSurgeBoard from './SewerSurgeBoard.svelte';

	const context = getContext();
	onMount(() => (context.stateLayout.showLoadingScreen = true));
	context.eventEmitter.subscribeOnMount({
		buyBonusConfirm: () => { stateModal.modal = { name: 'buyBonusConfirm' }; },
	});
</script>

<App>
	<EnableSound />
	<EnableHotkey />
	<EnableGameActor />
	<EnablePixiExtension />
	<ResumeBet />
	<UI>
		{#snippet gameName()}
			<UiGameName name="SEWER SURGE" />
		{/snippet}
		{#snippet logo()}
			<Text
				anchor={{ x: 1, y: 0 }}
				text="KINGWIN"
				style={{ fontFamily: 'proxima-nova', fontSize: REM * 1.25, fontWeight: '800', lineHeight: REM * 2, fill: 0x9cffb0 }}
			/>
		{/snippet}
	</UI>
	<SewerSurgeWin />
</App>

<SewerSurgeBoard />

{#if context.stateLayout.showLoadingScreen}
	<LoadingScreen onloaded={() => (context.stateLayout.showLoadingScreen = false)} />
{/if}

<Modals>
	{#snippet version()}
		<GameVersion version="0.1.0" />
	{/snippet}
</Modals>
