import { useState, useEffect } from "react";
import axios from "axios";
import Hand from "./blackjack/Hand";
import Hud from "./blackjack/Hud";
import "./Tutorial.css";

// ── Step definitions ───────────────────────────────────────────
const STEPS = [
  {
    id:        "welcome",
    title:     "Welcome to Tutorial Mode",
    body:      "This walkthrough will guide you through a complete hand of Blackjack. Follow each step and you'll be ready to play on your own. Click Next to begin.",
    highlight: null,
    action:    "next",
  },
  {
    id:        "betting",
    title:     "Step 1 — Place a Bet",
    body:      "Before each round you must place a bet. Click the +$50 button to add chips to your bet. You can add multiple chip amounts — your total bet is shown in the middle.",
    highlight: "chip-row",
    action:    "bet",
  },
  {
    id:        "deal",
    title:     "Step 2 — Deal the Cards",
    body:      "Your bet is placed. Now click Deal to start the round. You and the dealer will each receive two cards — but one of the dealer's cards stays hidden until later.",
    highlight: "btn-deal",
    action:    "deal",
  },
  {
    id:        "your_hand",
    title:     "Step 3 — Your Hand",
    body:      "These are your cards. Your total is shown below them. The goal is to get as close to 21 as possible without going over — going over is called a Bust and means you automatically lose.",
    highlight: "player-zone",
    action:    "next",
  },
  {
    id:        "dealer_hand",
    title:     "Step 4 — The Dealer's Hand",
    body:      "The dealer has one card face up and one hidden. You can use the visible card to inform your strategy. The hidden card is revealed after you finish your turn.",
    highlight: "dealer-zone",
    action:    "next",
  },
  {
    id:        "hint",
    title:     "Step 5 — AI Strategy Hint",
    body:      "A.C.E. recommends the statistically optimal move for your hand. This is based on standard Blackjack basic strategy — a mathematically proven guide that minimizes the house edge.",
    highlight: "hint-banner",
    action:    "next",
  },
  {
    id:        "action",
    title:     "Step 6 — Make Your Move",
    body:      "Hit takes another card. Stand ends your turn. Double Down doubles your bet and gives you exactly one more card. Follow the AI hint or make your own choice.",
    highlight: "controls-playing",
    action:    "play",
  },
  {
    id:        "dealer_reveal",
    title:     "Step 7 — Dealer's Turn",
    body:      "The dealer reveals their hidden card and plays out their hand. The dealer must hit on any total of 16 or below and must stand on 17 or above — they have no choice.",
    highlight: "dealer-zone",
    action:    "next",
  },
  {
    id:        "result",
    title:     "Step 8 — The Result",
    body:      "The round is over. A standard win pays 1:1 — you get your bet back plus the same amount in winnings. A Blackjack (Ace + 10-value card on the first two cards) pays 3:2. A Push means you tied and your bet is returned.",
    highlight: "result-area",
    action:    "next",
  },
  {
    id:        "finish",
    title:     "You're Ready to Play!",
    body:      "You've completed the tutorial. You know how to bet, read your hand, use the strategy hints, and understand the outcome. Head back to the menu and start a real game.",
    highlight: null,
    action:    "finish",
  },
];

export default function Tutorial({ onNavigate, playerName, playerChips }) {
  const [step, setStep]             = useState(0);
  const [playerHand, setPlayerHand] = useState(null);
  const [dealerHand, setDealerHand] = useState(null);
  const [chips, setChips]           = useState(1000);
  const [bet, setBet]               = useState(0);
  const [hint, setHint]             = useState(null);
  const [outcome, setOutcome]       = useState(null);
  const [message, setMessage]       = useState("");
  const [loading, setLoading]       = useState(false);
  const [phase, setPhase]           = useState("betting");

  const current = STEPS[step];

  const restorePlayerSession = async () => {
    if (!playerName) return;
    try {
      await axios.post("/api/new-game", {
        name: playerName,
        restore_session: true,
        chips: playerChips,
      });
    } catch (err) {
      console.error("Failed to restore player session:", err);
    }
  };

  const handleExit = async () => {
    await restorePlayerSession();
    onNavigate("menu");
  };

  useEffect(() => {
    const initTutorial = async () => {
      try {
        await axios.post("/api/new-game", { name: "Tutorial", tutorial: true });
      } catch (err) {
        console.error("Failed to initialize tutorial session:", err);
      }
    };

    initTutorial();
    return () => {
      restorePlayerSession();
    };
  }, [playerName, playerChips]);

  const fetchHint = async () => {
    try {
      const res = await axios.get("/api/hint");
      setHint(res.data);
    } catch { setHint(null); }
  };

  // ── Step actions ─────────────────────────────────────────────
  const handleNext = () => setStep((s) => s + 1);

  const handleBet = () => {
    if (bet === 0) setBet(50);
    setStep((s) => s + 1);
  };

  const handleDeal = async () => {
  setLoading(true);
  try {
    const amount = bet > 0 ? bet : 50;
    const res    = await axios.post("/api/deal", { bet: amount });
    setPlayerHand(res.data.player_hand);
    setDealerHand(res.data.dealer_hand);
    setChips(res.data.chips);
    setBet(amount);
    setPhase("playing");
    await fetchHint();

    // If player has Blackjack, auto-resolve and skip to result
    if (res.data.player_hand.blackjack) {
      const standRes = await axios.post("/api/stand");
      setDealerHand(standRes.data.dealer_hand);
      setChips(standRes.data.chips);
      setOutcome(standRes.data.outcome);
      setMessage(standRes.data.message);
      setPhase("result");
      setStep(STEPS.findIndex(s => s.id === "result"));
    } else {
      setStep((s) => s + 1);
    }
  } catch { }
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
      setStep((s) => s + 1);
    } catch { }
    setLoading(false);
  };

  const handleHit = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/hit");
      setPlayerHand(res.data.player_hand);
      setChips(res.data.chips);

      // If bust during tutorial, silently deal a fresh hand
      if (res.data.bust) {
        const fresh = await axios.post("/api/deal", { bet: 50 });
        setPlayerHand(fresh.data.player_hand);
        setDealerHand(fresh.data.dealer_hand);
        setChips(fresh.data.chips);
        await fetchHint();
      } else {
        setStep((s) => s + 1);
        setPhase("result_pending");
        await handleStand();
        return;
      }
    } catch { }
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
      setStep((s) => s + 2); // skip dealer reveal, go to result
    } catch { }
    setLoading(false);
  };

  const outcomeColor = () => {
    if (!outcome) return "";
    if (outcome === "lose") return "result-lose";
    if (outcome === "push") return "result-push";
    return "result-win";
  };

  // ── Overlay button ────────────────────────────────────────────
  const renderOverlayAction = () => {
    switch (current.action) {
      case "next":
        return (
          <button className="tut-btn-next" onClick={handleNext}>
            {step === STEPS.length - 1 ? "Back to Menu" : "Next →"}
          </button>
        );
      case "bet":
        return (
          <button className="tut-btn-next" onClick={handleBet}>
            Place $50 Bet →
          </button>
        );
      case "deal":
        return (
          <button className="tut-btn-next" onClick={handleDeal} disabled={loading}>
            {loading ? "Dealing..." : "Deal Cards →"}
          </button>
        );
      case "play":
        return (
          <div className="tut-action-row">
            <button className="tut-action-btn" onClick={handleHit}    disabled={loading}>Hit</button>
            <button className="tut-action-btn" onClick={handleStand}  disabled={loading}>Stand</button>
            <button className="tut-action-btn" onClick={handleDouble} disabled={loading}>Double Down</button>
          </div>
        );
      case "finish":
        return (
          <button className="tut-btn-next" onClick={handleExit}>
            Back to Menu →
          </button>
        );
      default:
        return null;
    }
  };

  return (
    <div className="tut-root">
      <div className="table-felt" />

      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

<button className="table-menu-btn" onClick={handleExit}>
        ← Menu
      </button>

      {/* Progress bar */}
      <div className="tut-progress">
        {STEPS.map((s, i) => (
          <div
            key={s.id}
            className={`tut-dot ${i === step ? "tut-dot-active" : ""} ${i < step ? "tut-dot-done" : ""}`}
          />
        ))}
      </div>

      {/* Dealer zone */}
      <div className={`table-dealer-zone ${current.highlight === "dealer-zone" ? "tut-highlight" : ""}`} id="dealer-zone">
        <p className="zone-label">DEALER</p>
        {dealerHand
          ? <Hand cards={dealerHand.cards} total={phase === "result" ? dealerHand.total : "?"} />
          : <div className="zone-placeholder">Cards will appear here</div>}
      </div>

      <div className="table-divider" />

      {/* Player zone */}
      <div className={`table-player-zone ${current.highlight === "player-zone" ? "tut-highlight" : ""}`} id="player-zone">
        <p className="zone-label">YOUR HAND</p>
        {playerHand
          ? <Hand cards={playerHand.cards} total={playerHand.total} />
          : <div className="zone-placeholder">Your cards will appear here</div>}
      </div>

      <Hud chips={chips} bet={bet} />

      {/* Hint banner */}
      {hint && (
        <div className={`hint-banner ${current.highlight === "hint-banner" ? "tut-highlight" : ""}`} id="hint-banner">
          <span className="hint-icon">🤖</span>
          <span className="hint-text">
            <strong>{hint.action}</strong> — {hint.explanation}
          </span>
        </div>
      )}

      {/* Result */}
      {phase === "result" && (
        <div className={`tut-result ${current.highlight === "result-area" ? "tut-highlight" : ""}`} id="result-area">
          <span className={`result-message ${outcomeColor()}`}>{message}</span>
        </div>
      )}

      {/* Tutorial overlay panel */}
      <div className="tut-overlay">
        <div className="tut-step-label">Step {Math.max(step, 1)} of {STEPS.length - 1}</div>
        <h2 className="tut-title">{current.title}</h2>
        <p className="tut-body">{current.body}</p>
        <div className="tut-actions">
          {renderOverlayAction()}
        </div>
      </div>

    </div>
  );
}