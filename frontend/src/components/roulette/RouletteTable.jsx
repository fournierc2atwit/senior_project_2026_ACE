import "./RouletteTable.css";

export default function RouletteTable({ onNavigate, initialChips }) {
  return (
    <div className="roulette-root">
      <div className="roulette-felt" />
      <button className="table-menu-btn" onClick={() => onNavigate("menu")}>← Menu</button>

      <div className="roulette-stage">
        <div className="roulette-header">
          <h1>Roulette</h1>
          <p>Spin the wheel and place your bets. The table below is a visual placeholder for the roulette board.</p>
        </div>

        <div className="roulette-board">
          <div className="wheel-panel">
            <div className="wheel-ring">
              <span>0</span>
            </div>
            <p className="wheel-label">Wheel</p>
          </div>

          <div className="bets-panel">
            <div className="bets-summary">
              <span className="bets-label">Chips</span>
              <span className="bets-value">${(initialChips ?? 1000).toLocaleString()}</span>
            </div>
            <p className="bets-help">Select a game in the main menu to switch between Blackjack, Roulette, and Slots.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
