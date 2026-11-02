<script lang="ts">
  import { stateGame } from '../game/stateGame.svelte';
  import type { SewerPipeCell, SewerPipeType } from '../game/sewerSurgeTypes';

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
  const POINTS: Record<string, [number, number]> = {
    N: [50, 4], E: [96, 50], S: [50, 96], W: [4, 50],
  };

  let selectedBranches = $state<Record<string, string>>({});
  let previousRoundKey = $state('');
  const round = $derived(stateGame.sewerRound);
  const board = $derived(round?.board ?? []);
  const preferredBranches = $derived.by(() => findPreferredBranches(board, round?.inlet ?? 0));
  const route = $derived.by(() => buildRoute(board, round?.inlet ?? 0, selectedBranches, preferredBranches));
  const payoutText = $derived(round?.payoutCents == null ? '—' : `${(round.payoutCents / 100).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}×`);
  const featureText = $derived(round?.scatterTier === 'deep-run' ? 'DEEP RUN' : round?.scatterTier === 'bonus' ? 'BONUS RUN' : 'NO BONUS');
  const statusText = $derived(round ? 'SERVER-LOCKED ROUND · RGS' : 'AWAITING RGS ROUND');

  $effect(() => {
    const key = round ? `${round.bookId ?? 'round'}:${round.inlet}:${round.payoutCents}` : '';
    if (key !== previousRoundKey) {
      previousRoundKey = key;
      selectedBranches = {};
    }
  });

  function getPorts(cell: SewerPipeCell): string[] {
    return BASE_PORTS[cell.t].map((side) => DIRECTIONS[(DIRECTIONS.indexOf(side as (typeof DIRECTIONS)[number]) + cell.r) % 4]);
  }

  function isConnected(boardData: SewerPipeCell[][], row: number, col: number, direction: string): boolean {
    if (direction === 'E' && col === 4) return true;
    const [dx, dy] = STEP[direction];
    const nextCol = col + dx;
    const nextRow = row + dy;
    if (nextRow < 0 || nextRow >= 5 || nextCol < 0 || nextCol >= 5) return false;
    const neighbour = boardData[nextRow][nextCol];
    return getPorts(neighbour).includes(OPPOSITE[direction]);
  }

  function getOutgoing(boardData: SewerPipeCell[][], row: number, col: number, entry: string): string[] {
    const cellPorts = getPorts(boardData[row][col]);
    if (!cellPorts.includes(entry)) return [];
    return cellPorts.filter((direction) => direction !== entry && direction !== 'W' && isConnected(boardData, row, col, direction));
  }

  function findPreferredBranches(boardData: SewerPipeCell[][], inlet: number): Record<string, string> {
    // Find a default route that reaches the east outlet and passes through a
    // junction with at least two connected exits. Player choices only override
    // this local visual route; they are never transmitted to the RGS/math layer.
    const visited = new Set<string>();
    const branches: Record<string, string> = {};

    function search(row: number, col: number, entry: string, hasBranch: boolean): boolean {
      const key = `${row}:${col}`;
      if (visited.has(key)) return false;
      const options = getOutgoing(boardData, row, col, entry);
      visited.add(key);
      const branchExists = hasBranch || options.length > 1;

      for (const exit of options) {
        if (options.length > 1) branches[key] = exit;
        if (exit === 'E' && col === 4) {
          if (branchExists) return true;
        } else {
          const [dx, dy] = STEP[exit];
          if (search(row + dy, col + dx, OPPOSITE[exit], branchExists)) return true;
        }
        if (options.length > 1) delete branches[key];
      }

      visited.delete(key);
      return false;
    }

    search(inlet, 0, 'W', false);
    return branches;
  }

  function buildRoute(boardData: SewerPipeCell[][], inlet: number, selected: Record<string, string>, preferred: Record<string, string>) {
    const activeCells = new Set<string>();
    const incomingByCell = new Map<string, string>();
    const junctionOptions = new Map<string, string[]>();
    if (!boardData.length) return { activeCells, incomingByCell, junctionOptions, reachesOutlet: false };

    let row = inlet;
    let col = 0;
    let entry = 'W';
    let reachesOutlet = false;
    const visited = new Set<string>();

    for (let step = 0; step < 30; step += 1) {
      const key = `${row}:${col}`;
      if (visited.has(key)) break;
      visited.add(key);
      activeCells.add(key);
      incomingByCell.set(key, entry);
      const options = getOutgoing(boardData, row, col, entry);
      if (!options.length) break;
      if (options.length > 1) junctionOptions.set(key, options);
      const requested = selected[key] ?? preferred[key];
      const exit = requested && options.includes(requested) ? requested : options.includes('E') ? 'E' : options[0];
      if (exit === 'E' && col === 4) {
        reachesOutlet = true;
        break;
      }
      const [dx, dy] = STEP[exit];
      col += dx;
      row += dy;
      entry = OPPOSITE[exit];
      if (row < 0 || row >= 5 || col < 0 || col >= 5) break;
    }
    return { activeCells, incomingByCell, junctionOptions, reachesOutlet };
  }

  function chooseBranch(row: number, col: number) {
    const key = `${row}:${col}`;
    const options = route.junctionOptions.get(key) ?? [];
    if (options.length < 2) return;
    const current = selectedBranches[key] ?? preferredBranches[key];
    const currentIndex = options.indexOf(current);
    const nextIndex = (currentIndex + 1) % options.length;
    selectedBranches = { ...selectedBranches, [key]: options[nextIndex] };
  }

  function pipePath(direction: string) {
    const [x, y] = POINTS[direction];
    return `M50 50 L${x} ${y}`;
  }

  function cellLabel(cell: SewerPipeCell) {
    if (cell.t === 'S') return 'Scatter';
    if (cell.t === 'W') return 'Wild connector';
    return `${cell.t} pipe, rotation ${cell.r * 90} degrees`;
  }
</script>

<svelte:head>
  <title>Sewer Surge — KingWin</title>
  <meta name="description" content="Sewer Surge, a pipe-routing slot game by KingWin." />
</svelte:head>

<div class="sewer-stage" aria-label="Sewer Surge game board">
  <header class="topline">
    <div class="brand">
      <span class="brand-mark">KW</span>
      <div>
        <div class="eyebrow">KINGWIN ORIGINAL</div>
        <h1>SEWER <span>SURGE</span></h1>
      </div>
    </div>
    <div class="status-chip"><span class="pulse"></span> {statusText}</div>
  </header>

  <section class="mission-strip">
    <div><span class="eyebrow">SECTOR 05</span><strong>THE UNDERFLOW NETWORK</strong></div>
    <div class="flow-label"><span class="flow-dot"></span> WEST INLET <span class="flow-arrow">→</span> EAST OUTLET</div>
    <div class="scatter-meter">
      <span class="eyebrow">SCATTERS</span>
      <strong>{round?.scatterCount ?? '—'} <small>/ 25</small></strong>
    </div>
  </section>

  {#if round}
    <main class="board-shell">
      <div class="board-heading">
        <div><span class="eyebrow">LIVE PIPE GRID</span><strong>ROUTE THE CURRENT</strong></div>
        <div class="round-tag">ROUND AUTHORITATIVE <span>●</span></div>
      </div>
      <div class="board-wrap">
        <div class="edge-label inlet-label"><span>INLET</span><b>W</b></div>
        <div class="pipe-grid" role="grid" aria-label="Five by five pipe board">
          {#each board as row, rowIndex}
            {#each row as cell, colIndex}
              {@const key = `${rowIndex}:${colIndex}`}
              {@const active = route.activeCells.has(key)}
              {@const options = route.junctionOptions.get(key) ?? []}
              <div class:active class:scatter={cell.t === 'S'} class:wild={cell.t === 'W'} class="pipe-cell" role="gridcell" aria-label={`Row ${rowIndex + 1}, column ${colIndex + 1}: ${cellLabel(cell)}`}>
                {#if cell.t === 'S'}
                  <div class="scatter-glyph">✦</div>
                  <span class="cell-code">SCATTER</span>
                {:else}
                  <svg viewBox="0 0 100 100" aria-hidden="true">
                    <g transform={`rotate(${cell.r * 90} 50 50)`}>
                      {#each BASE_PORTS[cell.t] as direction}
                        <path d={pipePath(direction)} class:lit={active} />
                      {/each}
                      <circle cx="50" cy="50" r="12" />
                    </g>
                  </svg>
                  <span class="cell-code">{cell.t}{cell.t === 'W' ? ' · WILD' : ` · ${cell.r * 90}°`}</span>
                {/if}
                {#if options.length > 1}
                  <button class="branch-button" type="button" aria-label={`Choose branch at row ${rowIndex + 1}, column ${colIndex + 1}`} title={`Cycle branch: ${options.join(' / ')}`} onclick={() => chooseBranch(rowIndex, colIndex)}>
                    {selectedBranches[key] ?? '↗'}
                  </button>
                {/if}
              </div>
            {/each}
          {/each}
        </div>
        <div class="edge-label outlet-label"><span>OUTLET</span><b>E</b></div>
      </div>
      <div class="board-foot">
        <span><i class="key-dot active-dot"></i> LIT ROUTE</span>
        <span><i class="key-dot branch-dot"></i> CHOOSE A JUNCTION</span>
        <span class:connected={route.reachesOutlet} class:disconnected={!route.reachesOutlet}>{route.reachesOutlet ? 'FLOW REACHES OUTLET' : 'BRANCH ENDS HERE'}</span>
      </div>
    </main>
  {:else}
    <main class="waiting-shell">
      <div class="waiting-icon">⌁</div>
      <span class="eyebrow">AWAITING AUTHORITATIVE ROUND</span>
      <strong>PRESS SPIN TO START THE FLOW</strong>
      <p>The server will deal the 5×5 pipe network. Junction choices only change the visual water route.</p>
    </main>
  {/if}

  <footer class="instrument-panel">
    <div class="instrument"><span class="eyebrow">FEATURE STATUS</span><strong class:bonus={round?.scatterTier === 'bonus'} class:deep={round?.scatterTier === 'deep-run'}>{round ? featureText : 'STANDBY'}</strong></div>
    <div class="instrument pressure"><span class="eyebrow">WATER PRESSURE</span><strong>{round ? 'OPTIMAL' : '—'}</strong><div class="pressure-bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
    <div class="instrument payout"><span class="eyebrow">LOCKED ROUND AWARD</span><strong>{payoutText}</strong>{#if round?.maxWinCapped}<small>MAX WIN REACHED</small>{:else}<small>SERVER-SET · ROUTE-INDEPENDENT</small>{/if}</div>
  </footer>
  <p class="authority-note">YOUR ROUTE CHOICE ONLY LIGHTS THE PIPES. IT CANNOT CHANGE THE ROUND AWARD.</p>
</div>


<details class="sewer-rules">
  <summary>RULES</summary>
  <div class="rules-panel">
    <div class="rules-kicker">SEWER SURGE · GAME GUIDE</div>
    <h3>Route the water</h3>
    <p>The RGS supplies the round board and award before the animation plays. Choose a glowing junction to change the visual water path.</p>
    <p class="rules-warning">Your branch choice is visual only. It cannot change the payout or round result.</p>

    <h4>Pipe symbols</h4>
    <ul class="rules-grid">
      <li><b>I</b><span>Straight</span></li>
      <li><b>L</b><span>Elbow</span></li>
      <li><b>T</b><span>Tee junction</span></li>
      <li><b>X</b><span>Cross junction</span></li>
      <li><b>W</b><span>Wild connector · fixed</span></li>
      <li><b>S</b><span>Scatter</span></li>
    </ul>

    <h4>Scatter features</h4>
    <p><b>0–2 scatters:</b> no feature<br /><b>3 scatters:</b> Bonus<br /><b>4–5 scatters:</b> Deep Run</p>

    <h4>Bet modes</h4>
    <p>Base <b>1×</b> · Ante <b>3×</b><br />Normal Bonus Buy <b>100×</b><br />Super Bonus Buy <b>500×</b></p>

    <div class="rules-footer">
      <span>Maximum win</span><b>10,000×</b>
      <span>Configured RTP target</span><b>96.5% · pending verification</b>
    </div>
  </div>
</details>

<style>
  :global(html), :global(body) { background: #07100f; }
  .sewer-stage { position: fixed; z-index: 4; inset: 0; display: flex; flex-direction: column; align-items: center; padding: clamp(10px, 2vh, 22px) 16px 190px; color: #e6f1e9; font-family: Inter, ui-sans-serif, system-ui, sans-serif; pointer-events: none; background: radial-gradient(ellipse at 50% 44%, rgba(25, 94, 65, .22), transparent 52%); }
  .topline, .mission-strip, .board-shell, .instrument-panel, .waiting-shell, .authority-note { width: min(100%, 760px); }
  .topline { display: flex; align-items: center; justify-content: space-between; gap: 10px; pointer-events: none; }
  .brand { display: flex; align-items: center; gap: 10px; }
  .brand-mark { display: grid; place-items: center; width: 38px; height: 38px; border: 1px solid #537a62; border-radius: 9px; color: #a9ffbe; font-weight: 900; font-size: 13px; background: #10251c; box-shadow: 0 0 22px #2b9d5a33; }
  .eyebrow { display: block; color: #7c9b88; font-size: 9px; font-weight: 800; letter-spacing: .17em; }
  h1 { margin: 2px 0 0; font-size: clamp(18px, 3vw, 26px); line-height: 1; letter-spacing: .12em; font-weight: 950; }
  h1 span { color: #76f2a0; }
  .status-chip { padding: 8px 11px; border: 1px solid #30533f; border-radius: 99px; color: #9ec9aa; background: #091a13dd; font-size: 9px; font-weight: 800; letter-spacing: .08em; white-space: nowrap; }
  .pulse, .flow-dot { display: inline-block; width: 6px; height: 6px; margin-right: 6px; border-radius: 50%; background: #6df59a; box-shadow: 0 0 10px #6df59a; }
  .mission-strip { display: flex; align-items: center; justify-content: space-between; margin: clamp(10px, 2vh, 18px) 0 9px; padding: 9px 13px; border: 1px solid #243e31; border-radius: 9px; background: linear-gradient(90deg, #10241b, #0a1713); pointer-events: none; }
  .mission-strip strong { display: block; margin-top: 3px; font-size: 11px; letter-spacing: .09em; }
  .flow-label { color: #9ac9a7; font-size: 9px; font-weight: 850; letter-spacing: .12em; }
  .flow-arrow { margin: 0 5px; color: #76f2a0; font-size: 16px; }
  .scatter-meter { text-align: right; }
  .scatter-meter strong { font-size: 17px; color: #e5f4e8; }
  .scatter-meter small { color: #799382; font-size: 9px; }
  .board-shell { padding: 12px; border: 1px solid #335440; border-radius: 13px; background: linear-gradient(145deg, rgba(12, 31, 23, .96), rgba(5, 15, 13, .97)); box-shadow: 0 15px 50px #0009, inset 0 0 35px #5ed27b0a; pointer-events: auto; }
  .board-heading { display: flex; justify-content: space-between; align-items: center; margin-bottom: 9px; }
  .board-heading strong { display: block; margin-top: 3px; font-size: 12px; letter-spacing: .12em; }
  .round-tag { color: #8eb19a; font-size: 8px; font-weight: 850; letter-spacing: .12em; }
  .round-tag span { color: #70f39a; padding-left: 4px; }
  .board-wrap { display: grid; grid-template-columns: 36px minmax(0, 1fr) 36px; align-items: stretch; gap: 6px; }
  .edge-label { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 5px; color: #8ba995; font-size: 7px; font-weight: 850; letter-spacing: .12em; }
  .edge-label b { display: grid; place-items: center; width: 26px; height: 26px; border: 1px solid #6bba82; border-radius: 50%; color: #9bf8b0; font-size: 12px; background: #143321; box-shadow: 0 0 14px #5af48a3b; }
  .outlet-label b { border-color: #c1ab57; color: #f2d879; background: #30280e; box-shadow: 0 0 14px #ebc95122; }
  .pipe-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 5px; }
  .pipe-cell { position: relative; aspect-ratio: 1; min-width: 0; overflow: visible; border: 1px solid #284536; border-radius: 8px; background: linear-gradient(145deg, #10231b, #0a1713); box-shadow: inset 0 0 16px #0008; }
  .pipe-cell.active { border-color: #65e78b; box-shadow: 0 0 11px #5ff38a3a, inset 0 0 14px #4be47a18; }
  .pipe-cell svg { width: 100%; height: 82%; display: block; margin-top: 2%; overflow: visible; }
  .pipe-cell path { fill: none; stroke: #527866; stroke-width: 10; stroke-linecap: round; }
  .pipe-cell path.lit { stroke: #7aff9c; stroke-dasharray: 12 8; animation: waterFlow .75s linear infinite; filter: drop-shadow(0 0 5px #4bf37b); }
  @keyframes waterFlow { to { stroke-dashoffset: -20; } }
  @media (prefers-reduced-motion: reduce) { .pipe-cell path.lit { animation: none; } }
  .pipe-cell circle { fill: #193b29; stroke: #6c9c7a; stroke-width: 3; }
  .pipe-cell.active circle { fill: #79f79a; stroke: #d2ffdc; filter: drop-shadow(0 0 5px #66ff8f); }
  .pipe-cell.scatter { display: grid; place-items: center; background: linear-gradient(145deg, #3b3116, #17190e); border-color: #a99248; }
  .scatter-glyph { color: #ffe08a; font-size: clamp(24px, 4vw, 38px); line-height: 1; text-shadow: 0 0 15px #ffd75d; }
  .pipe-cell.wild { border-color: #498c94; background: linear-gradient(145deg, #10313a, #0b1d24); }
  .pipe-cell.wild circle { fill: #4bd5cf; stroke: #b8fff4; }
  .cell-code { position: absolute; bottom: 3px; left: 0; right: 0; text-align: center; color: #779384; font-size: clamp(5px, .8vw, 7px); font-weight: 850; letter-spacing: .09em; white-space: nowrap; }
  .scatter .cell-code { color: #d5bd75; }
  .branch-button { position: absolute; z-index: 1; top: -5px; right: -5px; display: grid; place-items: center; width: 24px; height: 24px; padding: 0; border: 1px solid #b1ffbe; border-radius: 50%; color: #0b1a11; background: #8cffaa; box-shadow: 0 0 15px #58f38499; font-size: 10px; font-weight: 950; cursor: pointer; pointer-events: auto; }
  .branch-button:hover { transform: scale(1.08); background: #c2ffd0; }
  .board-foot { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; margin-top: 9px; color: #86a391; font-size: 8px; font-weight: 850; letter-spacing: .08em; }
  .board-foot span { display: inline-flex; align-items: center; gap: 4px; }
  .key-dot { width: 6px; height: 6px; border-radius: 50%; background: #5b7867; }
  .active-dot { background: #78f39a; box-shadow: 0 0 8px #78f39a; }
  .branch-dot { background: #ffe08a; }
  .connected { color: #8dffab; }
  .disconnected { color: #e6c477; }
  .instrument-panel { display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: 7px; margin-top: 9px; pointer-events: none; }
  .instrument { min-width: 0; padding: 9px 11px; border: 1px solid #263e31; border-radius: 8px; background: #0a1913ed; }
  .instrument strong { display: block; margin-top: 4px; color: #d7e9dc; font-size: clamp(11px, 1.7vw, 15px); letter-spacing: .05em; }
  .instrument strong.bonus { color: #ffe08a; }
  .instrument strong.deep { color: #ffb46e; }
  .instrument.payout strong { color: #9cf9b2; font-size: clamp(16px, 2.8vw, 23px); font-weight: 950; }
  .instrument small { display: block; margin-top: 2px; color: #769181; font-size: 7px; font-weight: 800; letter-spacing: .1em; }
  .pressure-bars { display: flex; gap: 3px; height: 5px; margin-top: 6px; }
  .pressure-bars i { flex: 1; border-radius: 3px; background: #4dd77c; box-shadow: 0 0 7px #4dd77c55; }
  .authority-note { margin: 7px 0 0; color: #769181; text-align: center; font-size: 8px; font-weight: 850; letter-spacing: .12em; pointer-events: none; }
  .waiting-shell { flex: 1; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; margin: 12px 0; padding: 28px; border: 1px solid #2b4936; border-radius: 12px; text-align: center; background: linear-gradient(145deg, #10231b, #081511); pointer-events: none; }
  .waiting-icon { color: #82f4a0; font-size: 44px; line-height: 1; }
  .waiting-shell strong { font-size: clamp(14px, 2.4vw, 19px); letter-spacing: .1em; }
  .waiting-shell p { max-width: 430px; margin: 0; color: #81998a; font-size: 12px; line-height: 1.5; }

  @media (max-height: 700px) {
    .sewer-stage { padding-bottom: 150px; }
    .mission-strip { margin-top: 7px; margin-bottom: 6px; padding-top: 6px; padding-bottom: 6px; }
    .board-shell { padding: 8px; }
    .pipe-grid { gap: 3px; }
    .instrument-panel { margin-top: 6px; }
    .instrument { padding: 6px 8px; }
  }
  @media (max-width: 520px) {
    .sewer-stage { padding-left: 7px; padding-right: 7px; padding-bottom: 165px; }
    .status-chip { font-size: 7px; padding: 6px 8px; }
    .mission-strip { padding: 7px 8px; }
    .flow-label { font-size: 7px; }
    .board-shell { padding: 8px; }
    .board-wrap { grid-template-columns: 25px minmax(0, 1fr) 25px; gap: 3px; }
    .pipe-grid { gap: 3px; }
    .branch-button { width: 20px; height: 20px; font-size: 8px; }
    .instrument-panel { grid-template-columns: 1fr 1fr; }
    .instrument.payout { grid-column: 1 / -1; }
    .board-foot { font-size: 7px; }
  }

  .sewer-rules { position: fixed; z-index: 24; top: 12px; right: 12px; width: min(360px, calc(100vw - 24px)); color: #e8f7ed; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
  .sewer-rules > summary { display: inline-flex; align-items: center; justify-content: center; min-height: 38px; padding: 0 15px; border: 1px solid rgba(125, 255, 164, .55); border-radius: 8px; color: #b8ffd0; background: rgba(4, 17, 17, .92); box-shadow: 0 4px 22px rgba(0,0,0,.35); cursor: pointer; font-size: 10px; font-weight: 900; letter-spacing: .16em; list-style: none; }
  .sewer-rules > summary::-webkit-details-marker { display: none; }
  .sewer-rules[open] > summary { border-color: #8fffb1; background: #102b21; }
  .rules-panel { max-height: min(72vh, 640px); overflow: auto; margin-top: 8px; padding: 18px; border: 1px solid rgba(125, 255, 164, .42); border-radius: 12px; background: linear-gradient(155deg, rgba(12, 31, 27, .98), rgba(3, 12, 15, .98)); box-shadow: 0 16px 54px rgba(0,0,0,.72); font-size: 12px; line-height: 1.5; }
  .rules-kicker { color: #79d99b; font-size: 9px; font-weight: 900; letter-spacing: .18em; }
  .rules-panel h3 { margin: 6px 0 9px; color: #eaffef; font-size: 20px; font-weight: 900; }
  .rules-panel h4 { margin: 15px 0 6px; color: #9ce9b3; font-size: 10px; font-weight: 900; letter-spacing: .14em; text-transform: uppercase; }
  .rules-panel p { margin: 7px 0; color: #c2d8cc; }
  .rules-warning { padding: 9px 10px; border-left: 2px solid #75ee9b; border-radius: 4px; color: #caffd6 !important; background: rgba(84, 210, 125, .09); }
  .rules-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px 8px; padding: 0; margin: 0; list-style: none; }
  .rules-grid li { display: flex; align-items: center; gap: 7px; min-width: 0; color: #b4cbbd; font-size: 10px; }
  .rules-grid b { display: grid; place-items: center; width: 22px; height: 22px; flex: 0 0 22px; border: 1px solid rgba(127,255,164,.38); border-radius: 5px; color: #c8ffda; background: rgba(52,127,80,.22); font-size: 12px; }
  .rules-footer { display: grid; grid-template-columns: 1fr auto; gap: 5px 10px; margin-top: 15px; padding-top: 11px; border-top: 1px solid rgba(127,255,164,.18); color: #8da99a; font-size: 10px; }
  .rules-footer b { color: #d5ffe1; text-align: right; }
  @media (max-width: 520px) { .sewer-rules { top: 8px; right: 8px; width: min(320px, calc(100vw - 16px)); } .rules-panel { max-height: 65vh; padding: 14px; } }

</style>
