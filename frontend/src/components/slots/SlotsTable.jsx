import "./SlotsTable.css";

export default function SlotsTable({ onNavigate, initialChips }) {
  return (
    <div className="slots-root">
      <div className="slots-felt" />
      <button className="table-menu-btn" onClick={() => onNavigate("menu")}>← Menu</button>
      <div className="slots-panel">
        <div className="slots-header">
          <h1>Slots</h1>
          <p>Spin the reels and line up the symbols. This screen is a placeholder while the slots game UI is being built.</p>
        </div>

        <div className="slots-info">
          <div className="slots-summary">
            <span className="slots-summary-label">Starting chips</span>
            <span className="slots-summary-value">${(initialChips ?? 1000).toLocaleString()}</span>
          </div>
          <div className="slots-action-hint">
            <p>Select "Change Game" on the menu to try another experience while slots is under development.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
