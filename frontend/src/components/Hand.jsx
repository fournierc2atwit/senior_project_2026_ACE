import "./Hand.css";

const RED_SUITS = ["♥", "♦"];

function CardFace({ label }) {
  const suit     = label.slice(-1);
  const rank     = label.slice(0, -1);
  const isRed    = RED_SUITS.includes(suit);
  const isHidden = label === "?";

  if (isHidden) {
    return (
      <div className="card card-hidden">
        <div className="card-back-pattern" />
      </div>
    );
  }

  return (
    <div className={`card ${isRed ? "card-red" : "card-black"}`}>
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

export default function Hand({ cards, total }) {
  if (!cards || cards.length === 0) return null;

  const showTotal = total && total !== "?";

  return (
    <div className="hand-root">
      <div className="hand-cards">
        {cards.map((card, i) => (
          <CardFace key={i} label={card} />
        ))}
      </div>
      {showTotal && (
        <div className="hand-total">
          Total: <strong>{total}</strong>
        </div>
      )}
    </div>
  );
}