<script>
  import { traceFlow, openings } from './sewerGame.js';

  /**
   * Embeddable board view for an official Web SDK app.
   * Branch interaction changes only `picks` and the highlighted path.
   * There is deliberately no payout prop, payout callback, or bet API here.
   */
  export let round;
  export let interactive = true;
  export let label = 'SEWER SURGE PIPE NETWORK';
  export let onRouteChange = () => {};

  let picks = [];

  $: flow = round ? traceFlow(round.board, round.inlet, picks) : { path: [], junctions: [], end: 'dead' };
  $: activePath = new Set(flow.path);
  $: junctionCells = new Set(flow.junctions.map((junction) => junction.at));

  function changeBranch(index) {
    if (!interactive) return;
    const junctionIndex = flow.junctions.findIndex((junction) => junction.at === index);
    if (junctionIndex < 0) return;
    const junction = flow.junctions[junctionIndex];
    const next = flow.junctions.slice(0, junctionIndex).map((item) => item.chosen);
    next[junctionIndex] = (junction.chosen + 1) % junction.options.length;
    picks = next;
    onRouteChange({ end: traceFlow(round.board, round.inlet, picks).end, highlightedCells: traceFlow(round.board, round.inlet, picks).path });
  }

  function pipeLines(piece) {
    const dirs = openings(piece);
    const coords = { N: [50, 7], E: [93, 50], S: [50, 93], W: [7, 50] };
    return dirs.map((side) => ({ side, x: coords[side][0], y: coords[side][1] }));
  }
</script>

<section class="sewer-board-panel" aria-label={label}>
  <div class="sewer-board-heading">
    <span>{label}</span>
    <span class="board-flow-state">{flow.end === 'exit' ? 'OUTLET CONNECTED' : 'FLOW TRACE'}</span>
  </div>
  {#if round}
    <div class="sewer-board-frame">
      <div class="west-inlet" aria-label={`Water enters from west, row ${round.inlet + 1}`}>
        <span>IN</span><b>{String(round.inlet + 1).padStart(2, '0')}</b>
      </div>
      <div class="sewer-grid" role="grid" aria-label="Five by five pipe board">
        {#each round.board as piece, index}
          <div
            class:flow-active={activePath.has(index)}
            class:flow-junction={junctionCells.has(index)}
            class="pipe-cell"
            role="gridcell"
          >
            <svg viewBox="0 0 100 100" aria-hidden="true">
              {#each pipeLines(piece) as line}
                <line x1="50" y1="50" x2={line.x} y2={line.y} class="pipe-branch" />
              {/each}
              <circle cx="50" cy="50" r="15" class="pipe-core" />
              {#if piece.t === 'S'}
                <path d="M50 31 L55 44 L69 45 L58 55 L61 69 L50 62 L39 69 L42 55 L31 45 L45 44 Z" class="scatter-star" />
              {:else if piece.t === 'W'}
                <circle cx="50" cy="50" r="7" class="wild-core" />
              {/if}
            </svg>
            <span class="pipe-symbol">{piece.t}</span>
            {#if junctionCells.has(index) && interactive}
              <button class="junction-hit" type="button" aria-label={`Change visual route at pipe ${index + 1}`} onclick={() => changeBranch(index)}></button>
            {/if}
          </div>
        {/each}
      </div>
      <div class="east-outlet"><span>OUT</span><b>→</b></div>
    </div>
    <div class="sewer-board-footer">
      <span>SCATTERS: {round.scatters ?? round.scatterCount ?? 0}</span>
      <span>TIER: {(round.tier ?? round.scatterTier ?? 'none').toUpperCase()}</span>
      <span>ROUTE: VISUAL ONLY</span>
    </div>
  {:else}
    <div class="sewer-board-empty">Awaiting authoritative Math SDK board…</div>
  {/if}
</section>

<style>
  .sewer-board-panel { width: 100%; color: #d8f3dc; background: #101a17; border: 1px solid #315344; border-radius: 13px; padding: 14px; box-shadow: inset 0 0 40px #07110d; }
  .sewer-board-heading, .sewer-board-footer { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; font: 700 10px/1.2 ui-monospace, monospace; letter-spacing: .14em; color: #9db9a7; }
  .board-flow-state { color: #6ee7a2; }
  .sewer-board-frame { display: grid; grid-template-columns: 38px minmax(0, 1fr) 38px; align-items: center; gap: 5px; margin: 14px 0; }
  .west-inlet, .east-outlet { height: 100%; min-height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #71e8a4; background: #172920; border: 1px solid #37634b; border-radius: 7px; font: 700 9px/1 ui-monospace, monospace; }
  .west-inlet b, .east-outlet b { font-size: 16px; }
  .sewer-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px; padding: 5px; background: #080f0c; border: 1px solid #2e493b; border-radius: 8px; }
  .pipe-cell { position: relative; aspect-ratio: 1; min-width: 0; overflow: hidden; background: linear-gradient(145deg, #1b3025, #101a16 70%); border: 1px solid #294333; border-radius: 6px; }
  .pipe-cell svg { width: 100%; height: 100%; display: block; }
  .pipe-branch { stroke: #668b72; stroke-width: 13; stroke-linecap: round; fill: none; }
  .pipe-core { fill: #314c3b; stroke: #88a891; stroke-width: 5; }
  .wild-core { fill: #a9f5c3; stroke: #e3ffeb; stroke-width: 2; filter: drop-shadow(0 0 5px #65ff9c); }
  .scatter-star { fill: #e2bd64; stroke: #fff0ae; stroke-width: 2; filter: drop-shadow(0 0 5px #d8a444); }
  .pipe-symbol { position: absolute; right: 5px; bottom: 4px; padding: 2px 4px; border-radius: 3px; color: #adc8b4; background: #09120dce; font: 800 9px/1 ui-monospace, monospace; }
  .flow-active { border-color: #7cffaa; box-shadow: inset 0 0 17px #35ff8055, 0 0 7px #45ff8d55; }
  .flow-active .pipe-branch { stroke: #8affb4; filter: drop-shadow(0 0 5px #4dff94); }
  .flow-active .pipe-core { fill: #68ed9b; stroke: #c5ffda; }
  .flow-active .pipe-symbol { color: #e4ffed; }
  .flow-junction::after { content: '↗'; position: absolute; left: 4px; top: 3px; color: #e1c26e; text-shadow: 0 0 5px #edc35d; font: 900 10px/1 ui-monospace, monospace; pointer-events: none; }
  .junction-hit { position: absolute; inset: 0; z-index: 2; width: 100%; height: 100%; border: 0; background: transparent; cursor: pointer; }
  .junction-hit:focus-visible { outline: 2px solid #e7c872; outline-offset: -3px; }
  .sewer-board-footer { border-top: 1px solid #294333; padding-top: 10px; color: #759a82; font-size: 9px; }
  .sewer-board-empty { min-height: 240px; display: grid; place-items: center; color: #8bab96; font: 12px ui-monospace, monospace; }
  @media (max-width: 480px) { .sewer-board-panel { padding: 9px; } .sewer-board-frame { grid-template-columns: 28px minmax(0, 1fr) 28px; gap: 3px; } .sewer-grid { gap: 2px; padding: 3px; } .west-inlet, .east-outlet { min-height: 50px; } .sewer-board-footer { letter-spacing: .05em; } }
</style>
