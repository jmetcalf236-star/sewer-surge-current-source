<script lang="ts">
  import { getContext, onDestroy } from 'svelte';
  import { bookEventAmountToCurrencyString } from '@stake-engine/utils-shared/amount';
  import type { GameContext } from '../game/context';

  const context = getContext<GameContext>('game');

  let visible = $state(false);
  let amountText = $state('');
  let levelText = $state('WIN CONFIRMED');
  let completeCurrent: (() => void) | null = null;
  let timer: ReturnType<typeof setTimeout> | undefined;

  function finishWin() {
    const finish = completeCurrent;
    completeCurrent = null;
    if (timer) clearTimeout(timer);
    timer = undefined;
    visible = false;
    finish?.();
  }

  context.eventEmitter.subscribeOnMount({
    winShow: () => {
      visible = true;
    },
    winHide: () => {
      visible = false;
    },
    winUpdate: async (event: { amount: number; winLevelData?: { level?: number; name?: string; type?: string } }) => {
      visible = true;
      amountText = bookEventAmountToCurrencyString(event.amount);
      const level = Number(event.winLevelData?.level ?? 0);
      levelText = event.winLevelData?.name ?? event.winLevelData?.type ?? (level >= 4 ? 'PRESSURE BREAK' : 'WIN CONFIRMED');
      const displayDuration = level >= 4 ? 2200 : level >= 2 ? 1500 : 900;

      await new Promise<void>((resolve) => {
        completeCurrent = () => resolve();
        timer = setTimeout(() => {
          const finish = completeCurrent;
          completeCurrent = null;
          timer = undefined;
          visible = false;
          finish?.();
        }, displayDuration);
      });
    },
  });

  onDestroy(() => {
    if (timer) clearTimeout(timer);
    const finish = completeCurrent;
    completeCurrent = null;
    finish?.();
  });
</script>

{#if visible}
  <div class="sewer-win-overlay" role="status" aria-live="polite">
    <div class="win-scanline"></div>
    <section class="win-panel">
      <div class="win-kicker"><span class="pulse"></span> SEWER SURGE · RGS AWARD</div>
      <div class="win-level">{levelText}</div>
      <div class="win-amount">{amountText}</div>
      <div class="win-subtitle">ROUND RESULT CONFIRMED</div>
      <button type="button" class="continue-button" onclick={finishWin}>CONTINUE</button>
    </section>
  </div>
{/if}

<style>
  .sewer-win-overlay {
    position: fixed;
    inset: 0;
    z-index: 30;
    display: grid;
    place-items: center;
    padding: 24px;
    background: radial-gradient(circle at center, rgba(14, 47, 37, .72), rgba(2, 8, 9, .94) 68%);
    color: #e8f7ed;
    pointer-events: auto;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    backdrop-filter: blur(5px);
  }
  .win-scanline {
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: .22;
    background: repeating-linear-gradient(to bottom, transparent 0 4px, rgba(117, 255, 158, .08) 5px, transparent 6px);
  }
  .win-panel {
    position: relative;
    width: min(560px, 100%);
    padding: clamp(28px, 6vw, 56px);
    text-align: center;
    border: 1px solid rgba(112, 255, 159, .55);
    border-radius: 18px;
    background: linear-gradient(155deg, rgba(18, 39, 34, .98), rgba(5, 15, 17, .98));
    box-shadow: 0 0 0 1px rgba(112, 255, 159, .12), 0 22px 90px rgba(0, 0, 0, .72), 0 0 55px rgba(70, 255, 135, .18);
    animation: winEnter .3s ease-out both;
  }
  .win-kicker { display: flex; align-items: center; justify-content: center; gap: 9px; color: #8ed5a4; font-size: 11px; letter-spacing: .18em; font-weight: 800; }
  .pulse { width: 7px; height: 7px; border-radius: 50%; background: #70ff9a; box-shadow: 0 0 13px #70ff9a; }
  .win-level { margin-top: 24px; color: #c6ffd4; font-size: clamp(18px, 3vw, 26px); font-weight: 900; letter-spacing: .12em; text-transform: uppercase; }
  .win-amount { margin-top: 10px; color: #f1fff4; font-size: clamp(42px, 9vw, 76px); line-height: 1; font-weight: 950; letter-spacing: -.045em; text-shadow: 0 0 28px rgba(108, 255, 145, .4); overflow-wrap: anywhere; }
  .win-subtitle { margin-top: 20px; color: #85a997; font-size: 10px; font-weight: 800; letter-spacing: .24em; }
  .continue-button { margin-top: 30px; min-width: 150px; border: 1px solid rgba(126, 255, 166, .7); border-radius: 9px; padding: 12px 22px; color: #082015; background: linear-gradient(135deg, #a0ffc0, #51d982); font-weight: 900; letter-spacing: .14em; cursor: pointer; }
  .continue-button:hover { filter: brightness(1.08); }
  @keyframes winEnter { from { opacity: 0; transform: translateY(12px) scale(.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
  @media (prefers-reduced-motion: reduce) { .win-panel { animation: none; } }
</style>
