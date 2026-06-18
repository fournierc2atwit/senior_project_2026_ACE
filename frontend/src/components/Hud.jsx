import { useEffect, useRef, useState } from "react";
import "./Hud.css";

function useAnimatedCount(target) {
  const [display, setDisplay] = useState(target);
  const prev    = useRef(target);
  const frameRef = useRef(null);

  useEffect(() => {
    const start  = prev.current;
    const end    = target ?? 0;
    const diff   = end - start;
    const duration = 600;
    const startTime = performance.now();

    if (frameRef.current) cancelAnimationFrame(frameRef.current);

    const step = (now) => {
      const elapsed  = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased    = 1 - Math.pow(1 - progress, 3); // ease out cubic
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      } else {
        prev.current = end;
      }
    };

    frameRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target]);

  return display;
}

export default function Hud({ chips, bet }) {
  const displayChips = useAnimatedCount(chips ?? 1000);
  const displayBet   = bet ?? 0;

  return (
    <div className="hud-root">
      <div className="hud-item">
        <span className="hud-label">Chips</span>
        <span className="hud-value hud-chips">${displayChips.toLocaleString()}</span>
      </div>
      <div className="hud-divider" />
      <div className="hud-item">
        <span className="hud-label">Bet</span>
        <span className="hud-value hud-bet">${displayBet.toLocaleString()}</span>
      </div>
    </div>
  );
}