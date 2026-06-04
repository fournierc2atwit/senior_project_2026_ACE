import "./Hud.css";

export default function Hud({ chips, bet }) {
  const displayChips = chips ?? 1000;
  const displayBet   = bet   ?? 0;

  return (
    <div className="hud-root">
      <div className="hud-item">
        <span className="hud-label">Chips</span>
        <span className="hud-value hud-chips">${displayChips.toLocaleString()}</span>
      </div>
      <div className="hud-divider" />
      <div className="hud-item">
        <span className="hud-label">Bet</span>
        <span className="hud-value hud-bet">${displayBet.toLocaleString()}</span>
      </div>
    </div>
  );
}