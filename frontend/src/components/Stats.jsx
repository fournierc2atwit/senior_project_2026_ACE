import { useState, useEffect } from "react";
import axios from "axios";
import "./Stats.css";

export default function Stats({ onNavigate, playerName }) {
  const [playerStats, setPlayerStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState("");

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [statsRes, lbRes] = await Promise.all([
          axios.get("/api/stats"),
          axios.get("/api/leaderboard"),
        ]);
        setPlayerStats(statsRes.data);
        setLeaderboard(lbRes.data.leaderboard || []);
      } catch {
        setError("Failed to load stats.");
      }
      setLoading(false);
    };
    fetchAll();
  }, []);

  const winRate = (stats) => {
    if (!stats || stats.games_played === 0) return "0%";
    return `${Math.round((stats.wins / stats.games_played) * 100)}%`;
  };

  return (
    <div className="stats-root">
      <div className="stats-felt" />

      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

      <button className="table-menu-btn" onClick={() => onNavigate("menu")}>
        ← Menu
      </button>

      <div className="stats-content">
        <div className="stats-header">
          <h1 className="stats-title">Statistics</h1>
          <div className="stats-rule" />
        </div>

        {loading && <p className="stats-loading">Loading stats...</p>}
        {error   && <p className="stats-error">{error}</p>}

        {!loading && !error && playerStats && (
          <>
            {/* ── Player stats ── */}
            <div className="stats-section">
              <h2 className="stats-section-title">
                {playerStats.name
                  ? playerStats.name.charAt(0).toUpperCase() + playerStats.name.slice(1)
                  : "Your"}'s Stats
              </h2>

              {playerStats.all_time ? (
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">${playerStats.all_time.chips.toLocaleString()}</span>
                    <span className="stat-label">Chips</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{playerStats.all_time.games_played}</span>
                    <span className="stat-label">Games Played</span>
                  </div>
                  <div className="stat-card stat-card-green">
                    <span className="stat-value">{playerStats.all_time.wins}</span>
                    <span className="stat-label">Wins</span>
                  </div>
                  <div className="stat-card stat-card-red">
                    <span className="stat-value">{playerStats.all_time.losses}</span>
                    <span className="stat-label">Losses</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{playerStats.all_time.pushes}</span>
                    <span className="stat-label">Pushes</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{winRate(playerStats.all_time)}</span>
                    <span className="stat-label">Win Rate</span>
                  </div>
                  <div className="stat-card stat-card-dim">
                    <span className="stat-value">{playerStats.all_time.bankrupts}</span>
                    <span className="stat-label">Bankrupts</span>
                  </div>
                </div>
              ) : (
                <p className="stats-empty">No saved stats yet. Play a round to start tracking!</p>
              )}
            </div>

            {/* ── Leaderboard ── */}
            <div className="stats-section">
              <h2 className="stats-section-title">Leaderboard</h2>
              {leaderboard.length === 0 ? (
                <p className="stats-empty">No players on the leaderboard yet.</p>
              ) : (
                <div className="leaderboard">
                  <div className="lb-header">
                    <span className="lb-rank">#</span>
                    <span className="lb-name">Player</span>
                    <span className="lb-chips">Chips</span>
                    <span className="lb-played">Played</span>
                    <span className="lb-winrate">Win Rate</span>
                  </div>
                  {leaderboard.map((p, i) => {
                    const isCurrentPlayer =
                      p.player_name.toLowerCase() === (playerStats.name || "").toLowerCase();
                    return (
                      <div
                        key={p.player_name}
                        className={`lb-row ${isCurrentPlayer ? "lb-row-current" : ""}`}
                      >
                        <span className={`lb-rank ${i === 0 ? "lb-rank-gold" : i === 1 ? "lb-rank-silver" : i === 2 ? "lb-rank-bronze" : ""}`}>
                          {i === 0 ? "♛" : i + 1}
                        </span>
                        <span className="lb-name">
                          {p.player_name.charAt(0).toUpperCase() + p.player_name.slice(1)}
                          {isCurrentPlayer && <span className="lb-you"> (you)</span>}
                        </span>
                        <span className="lb-chips">${p.chips.toLocaleString()}</span>
                        <span className="lb-played">{p.games_played}</span>
                        <span className="lb-winrate">{p.win_percentage}%</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}