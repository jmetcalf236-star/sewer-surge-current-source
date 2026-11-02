<script>
  const cells = Array.from({ length: 25 }, (_, index) => index + 1);
  const scatterSlots = Array.from({ length: 5 }, (_, index) => index + 1);
</script>

<div class="preview-shell">
  <div class="stage" aria-label="Sewer Surge preview stage">
    <div class="title-plate">
      <div class="pipe pipe-left" aria-hidden="true"></div>
      <div class="title-copy">
        <span class="word sewer">SEWER</span>
        <span class="word surge">SURGE</span>
      </div>
      <div class="pipe pipe-right" aria-hidden="true"></div>
    </div>

    <aside class="panel payout-panel">
      <h2>PAYOUT TOTAL</h2>
      <div class="display-box">
        <span>0.00</span>
      </div>
      <div class="indicator-row" aria-label="Win indicators">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </div>
    </aside>

    <aside class="panel scatters-panel">
      <h2>SCATTERS</h2>
      <div class="scatter-row" aria-label="Scatter slots">
        {#each scatterSlots as slot}
          <span class:filled={slot <= 3}></span>
        {/each}
      </div>
    </aside>

    <div class="board-frame" aria-label="5 by 5 board mockup">
      <div class="board-grid">
        {#each cells as cell}
          <div class="tile" aria-label={`Board tile ${cell}`}></div>
        {/each}
      </div>
    </div>

    <div class="bottom-bar">
      <div class="utility-buttons">
        <button type="button">RULES</button>
        <button type="button">SOUND</button>
      </div>

      <div class="bet-panel" aria-label="Bet panel">
        <span class="label">BET</span>
        <div class="bet-controls">
          <button type="button" class="step">−</button>
          <span class="bet-value">5.00</span>
          <button type="button" class="step">+</button>
        </div>
      </div>

      <button type="button" class="spin-button">SPIN</button>

      <div class="reserve-panel" aria-label="Reserved panel">
        <span class="placeholder-label">RESERVED</span>
      </div>
    </div>
  </div>
</div>
