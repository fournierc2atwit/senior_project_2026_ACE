import { useState } from "react";
import axios from "axios";
import Hand from "./Hand";
import Hud from "./Hud";
import "./Table.css";

const CHIP_AMOUNTS = [10, 25, 50, 100];

export default function Table({ onNavigate, playerName, initialChips }) {
  const [phase, setPhase]           = useState("betting");
  const [playerHand, setPlayerHand] = useState(null);
  const [dealerHand, setDealerHand] = useState(null);
  const [chips, setChips]           = useState(initialChips ?? 1000);
  const [bet, setBet]               = useState(0);
  const [outcome, setOutcome]       = useState(null);
  const [message, setMessage]       = useState("");
  const [hint, setHint]             = useState(null);
  const [error, setError]           = useState("");
  const [loading, setLoading]       = useState(false);

  const clearError = () => setError("");

  const addChips = (amount) => {
    if (bet + amount > chips) return;
    setBet((b) => b + amount);
    clearError();
  };

  const clearBet = () => { setBet(0); clearError(); };

  const handleDeal = async () => {
    if (bet === 0) { setError("Place a bet first."); return; }
    setLoading(true);
    clearError();
    try {
      const res = await axios.post("/api/deal", { bet });
      setPlayerHand(res.data.player_hand);
      setDealerHand(res.data.dealer_hand);
      setChips(res.data.chips);
      setPhase("playing");
      fetchHint();
    } catch { setError("Failed to deal. Try again."); }
    setLoading(false);
  };

  const fetchHint = async () => {
    try {
      const res = await axios.get("/api/hint");
      setHint(res.data);
    } catch { setHint(null); }
  };

  const handleHit = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/hit");
      setPlayerHand(res.data.player_hand);
      setChips(res.data.chips);
      if (res.data.bust) {
        setOutcome("lose");
        setMessage("Bust — You lose.");
        setPhase("result");
        setHint(null);
      } else { fetchHint(); }
    } catch { setError("Failed to hit. Try again."); }
    setLoading(false);
  };

  const handleStand = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/stand");
      setDealerHand(res.data.dealer_hand);
      setChips(res.data.chips);
      setOutcome(res.data.outcome);
      setMessage(res.data.message);
      setPhase("result");
      setHint(null);
    } catch { setError("Failed to stand. Try again."); }
    setLoading(false);
  };

  const handleDouble = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/double");
      setPlayerHand(res.data.player_hand);
      setDealerHand(res.data.dealer_hand);
      setChips(res.data.chips);
      setOutcome(res.data.outcome);
      setMessage(res.data.message);
      setPhase("result");
      setHint(null);
    } catch { setError("Not enough chips to double down."); }
    setLoading(false);
  };

  const handleNextRound = () => {
    setPhase("betting");
    setPlayerHand(null);
    setDealerHand(null);
    setBet(0);
    setOutcome(null);
    setMessage("");
    setHint(null);
    clearError();
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/new-game", { name: playerName });
      setChips(res.data.chips);
      setBet(0);
      setOutcome(null);
      setMessage("");
      setPlayerHand(null);
      setDealerHand(null);
      setPhase("betting");
    } catch { setError("Failed to reset. Try again."); }
    setLoading(false);
  };

  const outcomeColor = () => {
    if (!outcome) return "";
    if (outcome === "lose") return "result-lose";
    if (outcome === "push") return "result-push";
    return "result-win";
  };

  const isBroke = chips === 0;

  const handleMenu = async () => {
    try {
      await axios.post("/api/save");
    } catch (err) {
      console.error("Failed to save before menu", err);
    }

    onNavigate("menu");
  };
  
  return (
    <div className="table-root">
      <div className="table-felt" />
      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

      <button className="table-menu-btn" onClick={handleMenu}>
        ← Menu
      </button>

      <div className="table-dealer-zone">
        <p className="zone-label">DEALER</p>
        {dealerHand
          ? <Hand cards={dealerHand.cards} total={dealerHand.total} />
          : <div className="zone-placeholder">Waiting for deal...</div>}
      </div>

      <div className="table-divider" />

      <div className="table-player-zone">
        <p className="zone-label">YOUR HAND</p>
        {playerHand
          ? <Hand cards={playerHand.cards} total={playerHand.total} bust={outcome === "lose" && playerHand?.bust} />
          : <div className="zone-placeholder">Place your bet to begin</div>}
      </div>

      <Hud chips={chips} bet={bet} />

      {hint && phase === "playing" && (
        <div className="hint-banner">
          <span className="hint-icon">🤖</span>
          <span className="hint-text">
            <strong>{hint.action}</strong> — {hint.explanation}
          </span>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="table-controls">

        {phase === "betting" && (
          isBroke ? (
            <div className="controls-result">
              <div className="result-message result-lose">Out of chips!</div>
              <button className="btn-next" onClick={handleReset}>
                Start Over
              </button>
            </div>
          ) : (
            <div className="controls-betting">
              <div className="chip-row">
                {CHIP_AMOUNTS.map((amt) => (
                  <button key={amt} className="chip-btn" onClick={() => addChips(amt)}>
                    +${amt}
                  </button>
                ))}
              </div>
              <div className="bet-action-row">
                <button className="btn-clear" onClick={clearBet} disabled={bet === 0}>Clear</button>
                <div className="bet-display">Bet: <strong>${bet}</strong></div>
                <button
                  className={`btn-deal ${bet > 0 ? "btn-deal-active" : ""}`}
                  onClick={handleDeal}
                  disabled={bet === 0 || loading}
                >
                  {loading ? "Dealing..." : "Deal"}
                </button>
              </div>
            </div>
          )
        )}

        {phase === "playing" && (
          <div className="controls-playing">
            <button className="action-btn btn-hit"    onClick={handleHit}    disabled={loading}>Hit</button>
            <button className="action-btn btn-stand"  onClick={handleStand}  disabled={loading}>Stand</button>
            <button className="action-btn btn-double" onClick={handleDouble} disabled={loading}>Double Down</button>
          </div>
        )}

        {phase === "result" && (
          <div className="controls-result">
            <div className={`result-message ${outcomeColor()}`}>{message}</div>
            <button className="btn-next" onClick={handleNextRound}>Next Round</button>
          </div>
        )}

      </div>
    </div>
  );
}