import { useState, useEffect, useRef } from "react";
import axios from "axios";
import Hud from "../blackjack/Hud";
import "./RouletteTable.css";

const WHEEL_ORDER = [
  0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1, "00",
  27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2,
];

const RED_NUMBERS = new Set([
  1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36,
]);

const CHIP_AMOUNTS = [
  { value: 10,  img: "/chips/chip-10.png" },
  { value: 25,  img: "/chips/chip-25.png" },
  { value: 50,  img: "/chips/chip-50.png" },
  { value: 100, img: "/chips/chip-100.png" },
];

const SLICE_ANGLE      = 360 / WHEEL_ORDER.length;
const BASE_WHEEL_SIZE  = 340;
const EXTRA_SPINS      = 6;

function colorFor(num) {
  if (num === 0 || num === "00") return "green";
  return RED_NUMBERS.has(num) ? "red" : "black";
}

function angleForNumber(num) {
  const idx = WHEEL_ORDER.indexOf(num);
  return idx * SLICE_ANGLE + SLICE_ANGLE / 2;
}

const COLOR_HEX = {
  red:   "#a8332b",
  black: "#1a1a1a",
  green: "#1f7a3d",
};

function buildWheelGradient() {
  const stops = WHEEL_ORDER.map((num, i) => {
    const hex   = COLOR_HEX[colorFor(num)];
    const start = i * SLICE_ANGLE;
    const end   = (i + 1) * SLICE_ANGLE;
    return `${hex} ${start}deg ${end}deg`;
  });
  return `conic-gradient(from 0deg, ${stops.join(", ")})`;
}

const WHEEL_BACKGROUND = buildWheelGradient();
const STRAIGHT_NUMBERS = [0, "00", ...Array.from({ length: 36 }, (_, i) => i + 1)];

export default function RouletteTable({ onNavigate, playerName, initialChips, onSetChips }) {
  const [chips, setChips]       = useState(initialChips ?? 1000);
  const [amount, setAmount]     = useState(0);
  const [betType, setBetType]   = useState("color");
  const [betValue, setBetValue] = useState("red");
  const [rotation, setRotation] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState("");
  const wheelRef                = useRef(null);
  const [wheelRadius, setWheelRadius] = useState(0);

  useEffect(() => {
    if (!wheelRef.current) return;
    const rect = wheelRef.current.getBoundingClientRect();
    setWheelRadius(rect.width / 2 - 28);
  }, []);

  useEffect(() => {
    if (onSetChips) onSetChips(chips);
  }, [chips, onSetChips]);

  const clearError = () => setError("");

  const addChips = (amt) => {
    if (amount + amt > chips) return;
    setAmount((a) => a + amt);
    clearError();
  };

  const clearBet = () => { setAmount(0); clearError(); };

  const selectBetType = (type) => {
    setBetType(type);
    setBetValue(null);
    clearError();
  };

  const handleMenu = async () => {
    try { await axios.post("/api/save"); } catch {}
    onNavigate("menu");
  };

  const handleSpin = async () => {
    if (amount === 0)      { setError("Place a bet first.");        return; }
    if (betValue === null) { setError("Select a value to bet on."); return; }

    setLoading(true);
    setSpinning(true);
    clearError();
    setResult(null);

    try {
      const res = await axios.post("/api/roulette/spin", {
        bet_type:  betType,
        bet_value: betValue,
        amount,
      });

      const number = res.data.number;
      const target = angleForNumber(number);

      setRotation((prev) => {
        const baseFullTurns = Math.floor(prev / 360) * 360;
        const remainder     = ((360 - target) % 360 + 360) % 360;
        return baseFullTurns + EXTRA_SPINS * 360 + remainder + 360;
      });

      setTimeout(() => {
        setResult(res.data);
        setChips(res.data.chips);
        setSpinning(false);
        setLoading(false);
      }, 3000);
    } catch {
      setError("Spin failed. Try again.");
      setSpinning(false);
      setLoading(false);
    }
  };

  const resultColor = () => {
    if (!result) return "";
    return result.won ? "result-win" : "result-lose";
  };

  return (
    <div className="rt-root">
      <div className="rt-felt" />
      <span className="suit-tl">♠</span>
      <span className="suit-tr">♥</span>
      <span className="suit-bl">♣</span>
      <span className="suit-br">♦</span>

      <button className="table-menu-btn" onClick={handleMenu}>← Menu</button>

      <Hud chips={chips} bet={amount} />

      {/* ── Main layout wrapper ── */}
      <div className="rt-layout">

        {/* ── Wheel ── */}
        <div className="rt-wheel-zone">
          <div className="rt-pointer" />
          <div
            className="rt-wheel"
            ref={wheelRef}
            style={{
              background: WHEEL_BACKGROUND,
              transform: `rotate(${rotation}deg)`,
              transition: spinning
                ? "transform 3s cubic-bezier(0.17, 0.67, 0.12, 0.99)"
                : "none",
            }}
          >
            {WHEEL_ORDER.map((num, i) => {
              const angle  = i * SLICE_ANGLE + SLICE_ANGLE / 2;
              const radius = wheelRadius || BASE_WHEEL_SIZE / 2 - 16;
              return (
                <span
                  key={`${num}-${i}`}
                  className="rt-wheel-label"
                  style={{
                    transform: `rotate(${angle}deg) translate(0, -${radius}px) rotate(${-angle}deg)`,
                  }}
                >
                  {num}
                </span>
              );
            })}
          </div>
        </div>

        {/* ── Result — always reserves space so layout doesn't shift ── */}
        <div className="rt-result-zone">
          {result && !spinning && (
            <>
              <div className={`rt-result-badge rt-badge-${result.color}`}>
                {result.number}
              </div>
              <div className={`result-message ${resultColor()}`}>
                {result.won ? `You win $${result.payout}!` : "No win this round."}
              </div>
            </>
          )}
        </div>

      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* ── Controls ── */}
      <div className="rt-controls">

        <div className="rt-bet-type-row">
          {["straight", "color", "parity", "dozen"].map((type) => (
            <button
              key={type}
              className={`rt-type-btn ${betType === type ? "rt-type-active" : ""}`}
              onClick={() => selectBetType(type)}
              disabled={spinning}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>

        <div className="rt-value-picker">
          {betType === "straight" && (
            <div className="rt-number-grid">
              {STRAIGHT_NUMBERS.map((num) => (
                <button
                  key={num}
                  className={`rt-number-btn rt-num-${colorFor(num)} ${betValue === num ? "rt-value-selected" : ""}`}
                  onClick={() => setBetValue(num)}
                  disabled={spinning}
                >
                  {num}
                </button>
              ))}
            </div>
          )}

          {betType === "color" && (
            <div className="rt-swatch-row">
              <button className={`rt-swatch rt-swatch-red ${betValue === "red" ? "rt-value-selected" : ""}`} onClick={() => setBetValue("red")} disabled={spinning}>Red</button>
              <button className={`rt-swatch rt-swatch-black ${betValue === "black" ? "rt-value-selected" : ""}`} onClick={() => setBetValue("black")} disabled={spinning}>Black</button>
            </div>
          )}

          {betType === "parity" && (
            <div className="rt-swatch-row">
              <button className={`rt-simple-btn ${betValue === "odd" ? "rt-value-selected" : ""}`} onClick={() => setBetValue("odd")} disabled={spinning}>Odd</button>
              <button className={`rt-simple-btn ${betValue === "even" ? "rt-value-selected" : ""}`} onClick={() => setBetValue("even")} disabled={spinning}>Even</button>
            </div>
          )}

          {betType === "dozen" && (
            <div className="rt-swatch-row">
              <button className={`rt-simple-btn ${betValue === 1 ? "rt-value-selected" : ""}`} onClick={() => setBetValue(1)} disabled={spinning}>1st 12</button>
              <button className={`rt-simple-btn ${betValue === 2 ? "rt-value-selected" : ""}`} onClick={() => setBetValue(2)} disabled={spinning}>2nd 12</button>
              <button className={`rt-simple-btn ${betValue === 3 ? "rt-value-selected" : ""}`} onClick={() => setBetValue(3)} disabled={spinning}>3rd 12</button>
            </div>
          )}
        </div>

        <div className="rt-chip-row">
          {CHIP_AMOUNTS.map(({ value, img }) => (
            <button key={value} className="chip-btn" onClick={() => addChips(value)} disabled={spinning} aria-label={`Bet $${value}`}>
              <img src={img} alt="chip" className="chip-img" />
            </button>
          ))}
        </div>

        <div className="rt-action-row">
          <button className="btn-clear" onClick={clearBet} disabled={amount === 0 || spinning}>Clear</button>
          <div className="bet-display">Bet: <strong>${amount}</strong></div>
          <button
            className={`btn-deal ${amount > 0 && betValue !== null ? "btn-deal-active" : ""}`}
            onClick={handleSpin}
            disabled={amount === 0 || betValue === null || loading}
          >
            {spinning ? "Spinning..." : "Spin"}
          </button>
        </div>

      </div>
    </div>
  );
}