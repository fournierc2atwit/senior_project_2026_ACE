import { useState, useEffect } from "react";
import axios from "axios";
import "./Menu.css";

export default function Menu({ onNavigate, onSetName, onSetChips }) {
  const [name, setName]         = useState("");
  const [chips, setChips]       = useState(null);
  const [greeting, setGreeting] = useState("");
  const [loading, setLoading]   = useState(false);
  const [ready, setReady]       = useState(false);

  useEffect(() => {
    setTimeout(() => setReady(true), 100);
  }, []);

  const handleStart = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post("/api/new-game", { name: name.trim() });
      setChips(res.data.chips);
      setGreeting(
        res.data.returning
          ? `Welcome back, ${res.data.name}.`
          : `Welcome, ${res.data.name}.`
      );
      onSetName(name.trim());
      onSetChips(res.data.chips);
    } catch (err) {
      console.error("Failed to start game:", err);
    }
    setLoading(false);
  };

  const isStarted = chips !== null;

  return (
    <div className={`menu-root ${ready ? "menu-ready" : ""}`}>
      <div className="menu-felt" />

      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

      <div className="menu-center">

        <div className="menu-logo-block">
          <div className="menu-logo-ace">A.C.E.</div>
          <div className="menu-logo-sub">AI Casino Education</div>
          <div className="menu-logo-rule" />
        </div>

        {!isStarted ? (
          <div className="menu-entry">
            <label className="menu-label">Enter your name to begin</label>
            <div className="menu-input-row">
              <input
                className="menu-input"
                type="text"
                placeholder="Your name..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleStart()}
                maxLength={24}
              />
              <button
                className="menu-btn-primary"
                onClick={handleStart}
                disabled={!name.trim() || loading}
              >
                {loading ? "Loading..." : "Start"}
              </button>
            </div>
          </div>
        ) : (
          <div className="menu-actions">
            <p className="menu-greeting">{greeting}</p>
            <p className="menu-chips">
              <span className="menu-chips-label">Chips</span>
              <span className="menu-chips-value">${chips.toLocaleString()}</span>
            </p>

            <div className="menu-buttons">
              <button className="menu-btn menu-btn-play" onClick={() => onNavigate("game")}>
                <span className="btn-icon">♠</span> Play
              </button>
              <button className="menu-btn menu-btn-tutorial" onClick={() => onNavigate("tutorial")}>
                <span className="btn-icon">?</span> Tutorial
              </button>
              <button className="menu-btn menu-btn-stats" onClick={() => onNavigate("stats")}>
                <span className="btn-icon">◈</span> Stats
              </button>
              <button className="menu-btn menu-btn-quit" onClick={() => window.close()}>
                <span className="btn-icon">✕</span> Quit
              </button>
            </div>
          </div>
        )}

        <p className="menu-tagline">Learn the game. Beat the odds.</p>
      </div>
    </div>
  );
}