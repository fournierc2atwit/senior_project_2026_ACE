import { useEffect, useRef, useState } from "react";
import axios from "axios";
import Hand from "./Hand";
import Hud from "./Hud";
import "./Table.css";

const CHIP_AMOUNTS = [
  { value: 10,  img: "/chips/chip-10.png" },
  { value: 25,  img: "/chips/chip-25.png" },
  { value: 50,  img: "/chips/chip-50.png" },
  { value: 100, img: "/chips/chip-100.png" },
];

export default function Table({ onNavigate, onSetChips, playerName, initialChips }) {
  const [phase, setPhase]                     = useState("betting");
  const [playerHand, setPlayerHand]           = useState(null);
  const [dealerHand, setDealerHand]           = useState(null);
  const [chips, setChips]                     = useState(initialChips ?? 1000);
  const [bet, setBet]                         = useState(0);
  const [outcome, setOutcome]                 = useState(null);
  const [message, setMessage]                 = useState("");
  const [hint, setHint]                       = useState(null);
  const [countAdvice, setCountAdvice]         = useState(null);
  const [error, setError]                     = useState("");
  const [loading, setLoading]                 = useState(false);
  const [handCount, setHandCount]             = useState(1);
  const [activeHandIndex, setActiveHandIndex] = useState(0);
  const [canSplit, setCanSplit]               = useState(false);
  const [handNote, setHandNote]               = useState("");
  const [completedHands, setCompletedHands]   = useState([]);
  const [completedHandResults, setCompletedHandResults] = useState([]);
  const [deckReshuffled, setDeckReshuffled]   = useState(false);
  const reshuffleTimerRef                     = useRef(null);
  const mountedRef                            = useRef(true);

  useEffect(() => {
    if (onSetChips) onSetChips(chips);
  }, [chips, onSetChips]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearTimeout(reshuffleTimerRef.current);
    };
  }, []);

  const clearError = () => setError("");

  const showReshuffleNotice = (data) => {
    if (!data.deck_reshuffled) return;
    clearTimeout(reshuffleTimerRef.current);
    setDeckReshuffled(true);
    reshuffleTimerRef.current = setTimeout(() => setDeckReshuffled(false), 2500);
  };

  const resultMessageFor = (data) => {
    if (data.player_hand?.blackjack) {
      return data.outcome === "push"
        ? "Blackjack! Dealer also has Blackjack — bet returned."
        : "Blackjack! You win 3:2!";
    }
    if (data.dealer_hand?.blackjack) return "Dealer has Blackjack. You lose.";
    return data.message;
  };

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
      if (!mountedRef.current) return;
      setPlayerHand(res.data.player_hand);
      setDealerHand(res.data.dealer_hand);
      setChips(res.data.chips);
      showReshuffleNotice(res.data);

      if ("outcome" in res.data) {
        setCompletedHands(res.data.player_hands ?? []);
        setCompletedHandResults(res.data.hand_results ?? []);
        setOutcome(res.data.outcome);
        setMessage(resultMessageFor(res.data));
        setPhase("result");
        setHint(null);
        setHandNote("");
        setLoading(false);
        return;
      }

      setHandCount(res.data.hand_count ?? 1);
      setActiveHandIndex(res.data.active_hand_index ?? 0);
      setCanSplit(res.data.can_split ?? false);
      setHandNote("");
      setPhase("playing");
      fetchHint();
    } catch {
      if (mountedRef.current) setError("Failed to deal. Try again.");
    }
    if (mountedRef.current) setLoading(false);
  };

  const fetchHint = async () => {
    try {
      const [hintResponse, countResponse] = await Promise.all([
        axios.get("/api/hint"),
        axios.get("/api/count-advice"),
      ]);
      if (mountedRef.current) {
        setHint(hintResponse.data);
        setCountAdvice(countResponse.data);
      }
    } catch {
      if (mountedRef.current) {
        setHint(null);
        setCountAdvice(null);
      }
    }
  };

  const processActionResponse = (res) => {
    setChips(res.data.chips);
    showReshuffleNotice(res.data);

    if ("outcome" in res.data) {
      if (res.data.player_hand) setPlayerHand(res.data.player_hand);
      if (res.data.dealer_hand) setDealerHand(res.data.dealer_hand);
      setCompletedHands(res.data.player_hands ?? []);
      setCompletedHandResults(res.data.hand_results ?? []);
      setOutcome(res.data.outcome);
      setMessage(resultMessageFor(res.data));
      setPhase("result");
      setHint(null);
      setHandNote("");
      return;
    }

    const movedToNextHand = res.data.active_hand_index !== activeHandIndex;
    setPlayerHand(res.data.player_hand);
    setHandCount(res.data.hand_count ?? handCount);
    setActiveHandIndex(res.data.active_hand_index ?? activeHandIndex);
    setCanSplit(res.data.can_split ?? false);

    if (res.data.bust && movedToNextHand) {
      setHandNote(`Hand ${activeHandIndex + 1} busted — moving to Hand ${res.data.active_hand_index + 1}.`);
    } else {
      setHandNote("");
    }

    fetchHint();
  };

  const handleAction = async (endpoint, errorMessage) => {
    setLoading(true);
    try {
      const res = await axios.post(endpoint);
      if (mountedRef.current) processActionResponse(res);
    } catch {
      if (mountedRef.current) setError(errorMessage);
    }
    if (mountedRef.current) setLoading(false);
  };

  const handleHit    = () => handleAction("/api/hit", "Failed to hit. Try again.");
  const handleStand  = () => handleAction("/api/stand", "Failed to stand. Try again.");
  const handleDouble = () => handleAction("/api/double", "Not enough chips to double down.");

  const handleSplit = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/split");
      if (!mountedRef.current) return;
      setPlayerHand(res.data.player_hand);
      setChips(res.data.chips);
      setHandCount(res.data.hand_count ?? 2);
      setActiveHandIndex(res.data.active_hand_index ?? 0);
      setCanSplit(res.data.can_split ?? false);
      setHandNote("Hand split! Playing Hand 1 first.");
      showReshuffleNotice(res.data);
      fetchHint();
    } catch {
      if (mountedRef.current) setError("Unable to split. Check your chips and try again.");
    }
    if (mountedRef.current) setLoading(false);
  };

  const handleNextRound = () => {
    setPhase("betting");
    setPlayerHand(null);
    setDealerHand(null);
    setBet(0);
    setOutcome(null);
    setMessage("");
    setHint(null);
    setHandCount(1);
    setActiveHandIndex(0);
    setCanSplit(false);
    setHandNote("");
    setCompletedHands([]);
    setCompletedHandResults([]);
    clearError();
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/new-game", { name: playerName });
      if (!mountedRef.current) return;
      setChips(res.data.chips);
      setBet(0);
      setOutcome(null);
      setMessage("");
      setPlayerHand(null);
      setDealerHand(null);
      setHandCount(1);
      setActiveHandIndex(0);
      setCanSplit(false);
      setHandNote("");
      setCompletedHands([]);
      setCompletedHandResults([]);
      setPhase("betting");
    } catch {
      if (mountedRef.current) setError("Failed to reset. Try again.");
    }
    if (mountedRef.current) setLoading(false);
  };

  const outcomeColor = () => {
    if (!outcome) return "";
    if (outcome === "lose") return "result-lose";
    if (outcome === "push") return "result-push";
    return "result-win";
  };

  const isBroke = chips === 0;
  const canDouble = playerHand?.cards?.length === 2;

  const handleMenu = async () => {
    try { await axios.post("/api/save"); } catch (err) { console.error("Failed to save before menu", err); }
    onNavigate("menu");
  };

  return (
    <div className="table-root">
      <div className="table-felt" />
      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

      <button className="table-menu-btn" onClick={handleMenu}>← Menu</button>

      <Hud chips={chips} bet={bet} />

      {/* ── Centered play area ── */}
      <div className="table-play-area">

        <div className="table-dealer-zone">
          {dealerHand && dealerHand.total && dealerHand.total !== "?" && (
            <div className="hand-total dealer-total">Total: <strong>{dealerHand.total}</strong></div>
          )}
          <p className="zone-label">DEALER</p>
          {dealerHand
            ? <Hand cards={dealerHand.cards} total={dealerHand.total} showTotal={false} />
            : <div className="zone-idle"><div className="idle-card" /><div className="idle-card" /></div>}
        </div>

        <div className="table-divider" />

        <div className="table-player-zone">
          {phase === "result" && completedHands.length > 1 ? (
            <div className="split-result-hands">
              {completedHands.map((hand, index) => {
                const handResult = completedHandResults[index];
                return (
                  <div key={index} className="split-result-hand">
                    <Hand cards={hand.cards} total={hand.total} bust={hand.bust} />
                    <span className={`split-result-label split-result-${handResult}`}>
                      Hand {index + 1}: {handResult}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : playerHand
            ? <Hand cards={playerHand.cards} total={playerHand.total} bust={phase === "result" && outcome === "lose"} />
            : <div className="zone-idle"><div className="idle-card" /><div className="idle-card" /></div>}
          <p className="zone-label zone-label-below">
            YOUR HAND
            {handCount > 1 && completedHands.length <= 1 && (
              <span className="hand-indicator"> — Hand {activeHandIndex + 1} of {handCount}</span>
            )}
          </p>
        </div>

      </div>

      {/* ── Banners sit between play area and controls ── */}
      {handNote && phase === "playing" && (
        <div className="hand-note-banner">{handNote}</div>
      )}

      {hint && phase === "playing" && (
        <div className="hint-banner">
          <span className="hint-icon">🤖</span>
          <span className="hint-text">
            <strong>{hint.action}</strong> — {hint.explanation}
          </span>
        </div>
      )}

      {countAdvice && phase === "playing" && (
        <div className="count-banner">
          <span className="count-title">Hi-Lo Count</span>
          <span>RC {countAdvice.count.running_count >= 0 ? "+" : ""}{countAdvice.count.running_count}</span>
          <span>TC {countAdvice.count.true_count >= 0 ? "+" : ""}{countAdvice.count.true_count}</span>
          <span>{countAdvice.count.decks_remaining} decks left</span>
          <span className="count-action">Count says: {countAdvice.action}</span>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      {deckReshuffled && (
        <div className="deck-reshuffle-banner" role="status">Reshuffling Deck...</div>
      )}

      {/* ── Controls ── */}
      <div className="table-controls">

        {phase === "betting" && (
          isBroke ? (
            <div className="controls-result">
              <div className="result-message result-lose">You went bankrupt!</div>
              <button className="btn-next" onClick={handleReset}>Start Over</button>
            </div>
          ) : (
            <div className="controls-betting">
              <div className="chip-row">
                {CHIP_AMOUNTS.map(({ value, img }) => (
                  <button key={value} className="chip-btn" onClick={() => addChips(value)} aria-label={`Bet $${value}`}>
                    <img src={img} alt="chip" className="chip-img" />
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
            <button className="action-btn btn-double" onClick={handleDouble} disabled={loading || !canDouble}>Double Down</button>
            {canSplit && (
              <button className="action-btn btn-split" onClick={handleSplit} disabled={loading}>Split</button>
            )}
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
