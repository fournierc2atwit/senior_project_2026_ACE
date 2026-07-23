import { useState, useEffect } from "react";
import axios from "axios";
import "./Stats.css";

export default function Stats({ onNavigate, playerName }) {
  const [playerStats, setPlayerStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState("");

  useEffect(() => {
    let cancelled = false;

    const fetchAll = async () => {
      setLoading(true);
      try {
        const [statsRes, lbRes] = await Promise.all([
          axios.get("/api/stats"),
          axios.get("/api/leaderboard"),
        ]);
        if (cancelled) return;
        setPlayerStats(statsRes.data);
        setLeaderboard(lbRes.data.leaderboard || []);
      } catch {
        if (cancelled) return;
        setError("Failed to load stats.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchAll();

    return () => {
      cancelled = true;
    };
  }, []);

  const winRate = (stats) => {
    if (!stats || stats.games_played === 0) return "0%";
    return `${Math.round((stats.wins / stats.games_played) * 100)}%`;
  };

  const statsToShow = playerStats?.blackjack || playerStats?.all_time || null;
  const slotsStats = playerStats?.slots || {
    spins: 0,
    wins: 0,
    losses: 0,
    total_wagered: 0,
    total_payout: 0,
    biggest_win: 0,
    net_profit: 0,
    win_percentage: 0,
  };
  const rouletteStats = playerStats?.roulette || {
    spins: 0,
    wins: 0,
    losses: 0,
    total_wagered: 0,
    total_payout: 0,
    biggest_win: 0,
    net_profit: 0,
    win_percentage: 0,
    straight_bets: 0,
    color_bets: 0,
    parity_bets: 0,
    dozen_bets: 0,
  };

  const chips = playerStats?.shared?.chips ?? 0;
  const bankrupts = playerStats?.shared?.bankrupts ?? 0;

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

              {statsToShow ? (
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">${chips.toLocaleString()}</span>
                    <span className="stat-label">Chips</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{statsToShow.games_played}</span>
                    <span className="stat-label">Games Played</span>
                  </div>
                  <div className="stat-card stat-card-green">
                    <span className="stat-value">{statsToShow.wins}</span>
                    <span className="stat-label">Wins</span>
                  </div>
                  <div className="stat-card stat-card-red">
                    <span className="stat-value">{statsToShow.losses}</span>
                    <span className="stat-label">Losses</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{statsToShow.pushes}</span>
                    <span className="stat-label">Pushes</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{winRate(statsToShow)}</span>
                    <span className="stat-label">Win Rate</span>
                  </div>
                  <div className="stat-card stat-card-dim">
                    <span className="stat-value">{bankrupts}</span>
                    <span className="stat-label">Bankrupts</span>
                  </div>
                </div>
              ) : (
                <p className="stats-empty">No saved stats yet. Play a round to start tracking!</p>
              )}
            </div>

            {/* ── Game summaries ── */}
            <div className="stats-section">
              <h2 className="stats-section-title">Game Summaries</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-card-title">Blackjack</span>
                  <span className="stat-value">{statsToShow.games_played}</span>
                  <span className="stat-label">Games Played</span>
                  <span className="stat-label">Wins: {statsToShow.wins}</span>
                  <span className="stat-label">Losses: {statsToShow.losses}</span>
                  <span className="stat-label">Pushes: {statsToShow.pushes}</span>
                  <span className="stat-label">Win Rate: {winRate(statsToShow)}</span>
                </div>
                <div className="stat-card">
                  <span className="stat-card-title">Slots</span>
                  <span className="stat-value">{slotsStats.spins}</span>
                  <span className="stat-label">Spins</span>
                  <span className="stat-label">Wins: {slotsStats.wins}</span>
                  <span className="stat-label">Losses: {slotsStats.losses}</span>
                  <span className="stat-label">Wagered: ${slotsStats.total_wagered.toLocaleString()}</span>
                  <span className="stat-label">Payout: ${slotsStats.total_payout.toLocaleString()}</span>
                  <span className="stat-label">Net: ${slotsStats.net_profit.toLocaleString()}</span>
                  <span className="stat-label">Win Rate: {slotsStats.win_percentage}%</span>
                </div>
                <div className="stat-card">
                  <span className="stat-card-title">Roulette</span>
                  <span className="stat-value">{rouletteStats.spins}</span>
                  <span className="stat-label">Spins</span>
                  <span className="stat-label">Wins: {rouletteStats.wins}</span>
                  <span className="stat-label">Losses: {rouletteStats.losses}</span>
                  <span className="stat-label">Wagered: ${rouletteStats.total_wagered.toLocaleString()}</span>
                  <span className="stat-label">Payout: ${rouletteStats.total_payout.toLocaleString()}</span>
                  <span className="stat-label">Net: ${rouletteStats.net_profit.toLocaleString()}</span>
                  <span className="stat-label">Win Rate: {rouletteStats.win_percentage}%</span>
                </div>
              </div>
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
