import { useRef, useEffect } from "react";
import "./Hand.css";

const RED_SUITS  = ["♥", "♦"];
const SHORT_RANK = { "Jack": "J", "Queen": "Q", "King": "K", "Ace": "A" };

function CardFace({ label, index, isNewlyRevealed }) {
  const suit     = label.slice(-1);
  const fullRank = label.slice(0, -1);
  const rank     = SHORT_RANK[fullRank] || fullRank;
  const isRed    = RED_SUITS.includes(suit);
  const isHidden = label === "?";

  const dealDelay = `${index * 120}ms`;

  if (isHidden) {
    return (
      <div className="card card-hidden card-deal" style={{ animationDelay: dealDelay }}>
        <div className="card-back-pattern" />
      </div>
    );
  }

  return (
    <div
      className={`card ${isRed ? "card-red" : "card-black"} card-deal ${isNewlyRevealed ? "card-flip" : ""}`}
      style={{ animationDelay: isNewlyRevealed ? "0ms" : dealDelay }}
    >
      <div className="card-corner card-corner-tl">
        <span className="card-rank">{rank}</span>
        <span className="card-suit-sm">{suit}</span>
      </div>
      <div className="card-center-suit">{suit}</div>
      <div className="card-corner card-corner-br">
        <span className="card-rank">{rank}</span>
        <span className="card-suit-sm">{suit}</span>
      </div>
    </div>
  );
}

export default function Hand({ cards, total, bust, showTotal = true }) {
  const prevCards = useRef([]);
  const shouldShowTotal = showTotal && total && total !== "?";

  // Detect which card was just revealed (was "?" now is a real card)
  const revealedIndex = prevCards.current.findIndex(
    (c, i) => c === "?" && cards[i] && cards[i] !== "?"
  );

  useEffect(() => {
    prevCards.current = cards;
  }, [cards]);

  if (!cards || cards.length === 0) return null;

  return (
    <div className={`hand-root ${bust ? "hand-bust" : ""}`}>
      <div className="hand-cards">
        {cards.map((card, i) => (
          <CardFace
            key={`${card}-${i}`}
            label={card}
            index={i}
            isNewlyRevealed={i === revealedIndex}
          />
        ))}
      </div>
      {shouldShowTotal && (
        <div className="hand-total">
          Total: <strong>{total}</strong>
        </div>
      )}
    </div>
  );
}