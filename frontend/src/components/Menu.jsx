import { useState, useEffect } from "react";
import axios from "axios";
import "./Menu.css";

const GAME_OPTIONS = [
  { id: "blackjack", label: "Blackjack", emoji: "♠" },
  { id: "roulette", label: "Roulette", emoji: "◎" },
  { id: "slots", label: "Slots", emoji: "🎰" },
];

export default function Menu({ onNavigate, onSetName, onSetChips, onSetGame, selectedGame: initialGame, playerName: initialName, playerChips: initialChips }) {
  const [name, setName]         = useState(initialName || "");
  const [chips, setChips]       = useState(initialChips ?? null);
  const [greeting, setGreeting] = useState("");
  const [loading, setLoading]   = useState(false);
  const [ready, setReady]       = useState(false);
  const [selectedGame, setSelectedGame] = useState(initialGame || "blackjack");
  const [gameMenuOpen, setGameMenuOpen] = useState(false);

  useEffect(() => {
    setName(initialName || "");
  }, [initialName]);

  useEffect(() => {
    setChips(initialChips ?? null);
  }, [initialChips]);

  useEffect(() => {
    if (name && chips !== null) {
      setGreeting(`Welcome back, ${name}.`);
    }
  }, [name, chips]);

  useEffect(() => {
    setTimeout(() => setReady(true), 100);
  }, []);

  useEffect(() => {
    if (onSetGame) onSetGame(selectedGame);
  }, [onSetGame, selectedGame]);

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

            {!gameMenuOpen ? (
              <>
                <div className="menu-buttons">
                  <button className="menu-btn menu-btn-play" onClick={() => setGameMenuOpen(true)}>
                    <span className="btn-icon">▶</span> Play
                  </button>
                  <button className="menu-btn menu-btn-tutorial" onClick={() => onNavigate("tutorial") }>
                    <span className="btn-icon">?</span> Tutorial
                  </button>
                  <button className="menu-btn menu-btn-stats" onClick={() => onNavigate("stats") }>
                    <span className="btn-icon">◈</span> Stats
                  </button>
                  <button className="menu-btn menu-btn-quit" onClick={() => window.close()}>
                    <span className="btn-icon">✕</span> Quit
                  </button>
                </div>
              </>
            ) : (
              <div className="menu-game-list">
                <p className="game-list-heading">Choose a game:</p>
                {GAME_OPTIONS.map((game) => (
                  <button
                    key={game.id}
                    type="button"
                    className={`menu-btn game-list-button ${selectedGame === game.id ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedGame(game.id);
                      setGameMenuOpen(false);
                      onNavigate("game", game.id);
                    }}
                  >
                    <span className="btn-icon">{game.emoji}</span>
                    {game.label}
                  </button>
                ))}
                <button className="menu-btn game-list-button game-list-cancel" onClick={() => setGameMenuOpen(false)}>
                  Back
                </button>
              </div>
            )}
          </div>
        )}

        <p className="menu-tagline">Learn the game. Beat the odds.</p>
      </div>
    </div>
  );
}