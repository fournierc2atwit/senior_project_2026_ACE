import { useState, useEffect, useRef } from "react";
import axios from "axios";
import Hud from "../blackjack/Hud";
import "./SlotsTable.css";

const BET_TIERS = [25, 50, 100, 250];

const SYMBOL_ICONS = {
  cherry:  "🍒",
  lemon:   "🍋",
  bell:    "🔔",
  star:    "⭐",
  diamond: "💎",
  seven:   "7️⃣",
};

const PAYOUT_TABLE = [
  { symbol: "seven",   label: "Seven",   icon: "7️⃣", multiplier: 25 },
  { symbol: "diamond", label: "Diamond", icon: "💎", multiplier: 12 },
  { symbol: "star",    label: "Star",    icon: "⭐", multiplier: 8  },
  { symbol: "bell",    label: "Bell",    icon: "🔔", multiplier: 5  },
  { symbol: "lemon",   label: "Lemon",   icon: "🍋", multiplier: 4  },
  { symbol: "cherry",  label: "Cherry",  icon: "🍒", multiplier: 3  },
];

const SPIN_DURATIONS = [1200, 1600, 2000]; // staggered stop times per reel

export default function SlotMachine({ onNavigate, playerName, initialChips, onSetChips }) {
  const [chips, setChips]       = useState(initialChips ?? 1000);
  const [amount, setAmount]     = useState(BET_TIERS[0]);
  const [spinning, setSpinning] = useState(false);
  const [reels, setReels]       = useState(["cherry", "cherry", "cherry"]);
  const [reelSpinning, setReelSpinning] = useState([false, false, false]);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [advice, setAdvice]     = useState(null);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const mountedRef               = useRef(true);
  const spinTimersRef            = useRef([]);

  useEffect(() => {
    mountedRef.current = true;
    const spinTimers = spinTimersRef.current;

    return () => {
      mountedRef.current = false;
      spinTimers.forEach(clearTimeout);
    };
  }, []);

  const clearError = () => setError("");

  useEffect(() => {
    setAdvice(null);
  }, [amount]);

  const handleMenu = async () => {
    try { await axios.post("/api/save"); } catch {}
    onNavigate("menu");
  };

  const handleAdvice = async () => {
    setAdviceLoading(true);
    clearError();
    try {
      const res = await axios.post("/api/slots/advice", { amount });
      if (mountedRef.current) setAdvice(res.data.advice);
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err.response?.data?.message || "Advice is unavailable right now.");
    } finally {
      if (mountedRef.current) setAdviceLoading(false);
    }
  };

  const handleSpin = async () => {
    setLoading(true);
    setSpinning(true);
    setResult(null);
    clearError();
    setReelSpinning([true, true, true]);

    try {
      const res = await axios.post("/api/slots/spin", { amount });
      if (!mountedRef.current) return;

      const finalReels = res.data.reels;

      // Stop each reel in sequence at staggered times
      SPIN_DURATIONS.forEach((duration, i) => {
        const timer = setTimeout(() => {
          if (!mountedRef.current) return;
          setReels((prev) => {
            const next = [...prev];
            next[i] = finalReels[i];
            return next;
          });
          setReelSpinning((prev) => {
            const next = [...prev];
            next[i] = false;
            return next;
          });
        }, duration);
        spinTimersRef.current.push(timer);
      });

      // Reveal result after the last reel stops
      const resultTimer = setTimeout(() => {
        if (!mountedRef.current) return;
        setResult(res.data);
        setAdvice(res.data.advice_evaluation);
        setChips(res.data.chips);
        if (onSetChips) onSetChips(res.data.chips);
        setSpinning(false);
        setLoading(false);
      }, SPIN_DURATIONS[SPIN_DURATIONS.length - 1] + 200);
      spinTimersRef.current.push(resultTimer);

    } catch (err) {
      if (!mountedRef.current) return;
      const msg = err.response?.data?.message || "Spin failed. Try again.";
      setError(msg);
      setSpinning(false);
      setLoading(false);
      setReelSpinning([false, false, false]);
    }
  };

  const resultColor = () => {
    if (!result) return "";
    return result.won ? "result-win" : "result-lose";
  };

  return (
    <div className="sm-root">
      <div className="sm-felt" />
      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

      <button className="table-menu-btn" onClick={handleMenu}>
        ← Menu
      </button>

      <Hud chips={chips} bet={amount} />

      <div className="sm-content">

        {/* ── Machine ── */}
        <div className="sm-machine">
          <div className="sm-machine-header">A.C.E. SLOTS</div>

          <div className="sm-reel-window">
            {reels.map((symbol, i) => (
              <div key={i} className="sm-reel">
                <div className={`sm-reel-strip ${reelSpinning[i] ? "sm-spinning" : ""}`}>
                  {reelSpinning[i] ? (
                    <div className="sm-blur-symbols">
                      {Object.values(SYMBOL_ICONS).map((icon, j) => (
                        <span key={j} className="sm-symbol">{icon}</span>
                      ))}
                    </div>
                  ) : (
                    <span className="sm-symbol sm-symbol-final">
                      {SYMBOL_ICONS[symbol]}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="sm-payline" />
        </div>

        {/* ── Result ── */}
        {result && !spinning && (
          <div className="sm-result-zone">
            <div className={`result-message ${resultColor()}`}>
              {result.message}
            </div>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        {advice && (
          <div className="sm-advice" aria-live="polite">
            <p className="sm-advice-title">ACE Insight</p>
            <p>{advice.explanation}</p>
            {advice.lesson && <p>{advice.lesson}</p>}
            {advice.warnings?.map((warning) => (
              <p key={warning.code} className={`sm-advice-warning sm-advice-${warning.severity}`}>
                {warning.message}
              </p>
            ))}
          </div>
        )}

        {/* ── Bet tier selector ── */}
        <div className="sm-bet-row">
          {BET_TIERS.map((tier) => (
            <button
              key={tier}
              className={`sm-bet-btn ${amount === tier ? "sm-bet-active" : ""}`}
              onClick={() => { setAmount(tier); clearError(); }}
              disabled={spinning}
            >
              ${tier}
            </button>
          ))}
        </div>

        <div className="sm-action-row">
          <button
            className="sm-advice-btn"
            onClick={handleAdvice}
            disabled={spinning || adviceLoading || amount > chips}
          >
            {adviceLoading ? "Thinking..." : "Ask ACE"}
          </button>
          <button
            className={`btn-deal ${!spinning ? "btn-deal-active" : ""}`}
            onClick={handleSpin}
            disabled={loading || amount > chips}
          >
            {spinning ? "Spinning..." : "Spin"}
          </button>
        </div>

        {amount > chips && (
          <p className="sm-insufficient">Not enough chips for this bet.</p>
        )}

        {/* ── Payout table ── */}
        <div className="sm-payout-table">
          <p className="sm-payout-title">Payout Table</p>
          <div className="sm-payout-grid">
            {PAYOUT_TABLE.map((row) => (
              <div key={row.symbol} className="sm-payout-row">
                <span className="sm-payout-icons">
                  {row.icon}{row.icon}{row.icon}
                </span>
                <span className="sm-payout-mult">{row.multiplier}x</span>
              </div>
            ))}
            <div className="sm-payout-row">
              <span className="sm-payout-icons">🍒🍒 ?</span>
              <span className="sm-payout-mult">2x</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
