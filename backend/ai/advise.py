from ai.strategy import(
    get_raw_code,
    resolve_code,
    ACTION_NAMES,
)
 
_ACTION_ALIASES = {
    'h': 'H', 'hit': 'H',
    's': 'S', 'stand': 'S', 'stay': 'S',
    'd': 'D', 'double': 'D', 'double down': 'D', 'doubledown': 'D', 'dd': 'D',
    'p': 'P', 'split': 'P',
}
 
 
def _normalize_action(action):
    key = str(action).strip().lower()
    
    if key not in _ACTION_ALIASES:
        raise ValueError(
            f"Unknown action {action!r}. Use one of: hit, stand, double, split."
        )
    return _ACTION_ALIASES[key]
 
 
def _dealer_label(dealer_value):
    return "Ace" if dealer_value == 11 else str(dealer_value)
 
 
def _reason(action, raw_code, total, is_soft, is_pair, pair_value, dealer_value):
    d_label = _dealer_label(dealer_value)
    d_strong = dealer_value >= 7    # 7 through Ace; 2-6 are dealer "bust cards"
 
    # SPLIT
    if action == 'P':
        if pair_value == 11:
            return ("Always split Aces. Kept together they only make a soft 12, but "
                    "split into two hands each starting with an Ace you get two strong "
                    "chances to draw a ten and make 21.")
        if pair_value == 8:
            return ("Always split 8s. Together they make 16 — the worst total in "
                    "blackjack. Splitting trades one losing hand for two fresh hands "
                    "that each start with an 8.")
        return (f"Splitting beats playing one mediocre total here: the dealer's "
                f"{d_label} is weak and likely to bust, so you put more money out as "
                f"two separate hands while the dealer is in trouble.")
 
    # DOUBLE
    if action == 'D':
        if is_soft:
            return (f"Your hand is soft (the Ace counts as 11), so one more card can't "
                    f"bust you, and the dealer's {d_label} is weak — the ideal moment "
                    f"to put more money in while you're safe and the dealer is in "
                    f"trouble. Just remember you only get one card.")
        return (f"A total of {total} is a strong starting point and the dealer's "
                f"{d_label} is vulnerable, so you double your bet and take exactly one "
                f"more card while you're the favorite.")
 
    # STAND
    if action == 'S':
        if is_soft:
            return (f"A soft {total} is already strong against the dealer's {d_label}; "
                    f"taking another card risks turning a good hand into a worse one.")
        if total >= 17:
            return (f"A hard {total} is high enough that almost any card would bust "
                    f"you, so you keep it and let the dealer try to beat it.")
        # Stiff 12-16 against a weak dealer.
        return (f"Your {total} is a 'stiff' total that busts easily if you hit, and the "
                f"dealer's {d_label} is a bust card — so the smart play is to stand and "
                f"let the dealer risk going over 21.")
 
    # HIT
    if action == 'H':
        if total <= 8:
            return (f"With only {total} there's no card that can bust you, so you "
                    f"always take another to build your hand.")
        if total in (9, 10, 11) and not is_soft:
            if raw_code == 'D':
                return (f"A {total} is normally a doubling hand, but doubling isn't "
                        f"available right now, so the next-best play is to hit and try "
                        f"to reach a strong total.")
            return (f"A {total} is too low to stand on, and a single card often turns "
                    f"it into a 19, 20, or 21.")
        if is_soft:
            return (f"Your hand is soft (the Ace counts as 11), so one card can't bust "
                    f"you. Against the dealer's {d_label} this total isn't strong "
                    f"enough to stand on yet, so you draw to improve it.")
        if d_strong:
            return (f"Your {total} is a weak 'stiff' total and the dealer's {d_label} "
                    f"is strong — likely to finish with 17-21. Standing would probably "
                    f"lose, so you take the risk and hit to try to improve.")
        # 12 vs a 2 or 3: the genuinely close calls.
        return (f"{total} against the dealer's {d_label} is a close decision, but the "
                f"dealer isn't weak enough to count on a bust, so hitting wins slightly "
                f"more often over the long run.")
 
    return "No recommendation is available for this hand."
 
 
class Advisor:
    def __init__(self, rules="S17"):
        self.rules = rules
 
    # -- internal: pull every number the engine needs off the game objects ---
    def _read(self, player_hand, dealer_upcard, can_double, can_split):
        total = player_hand.get_value()
        is_soft = player_hand.is_soft()
        is_pair = player_hand.is_pair()
        pair_value = player_hand.cards[0].get_value() if is_pair else None
        dealer_value = dealer_upcard.get_value()
 
        # If the caller didn't say what's legal, derive it from the rules of
        # blackjack: you can only double or split on a fresh two-card hand.
        if can_double is None:
            can_double = (player_hand.card_count() == 2)
        if can_split is None:
            can_split = is_pair
 
        return total, is_soft, is_pair, pair_value, dealer_value, can_double, can_split
 
    def recommend(self, player_hand, dealer_upcard, can_double=None, can_split=None):
        """
        Return the optimal move for the current hand.
 
        Returns a dict:
            {
              "action":      'H' | 'S' | 'D' | 'P',
              "action_name": 'Hit' | 'Stand' | 'Double Down' | 'Split',
              "reason":      "<plain-English explanation>"
            }
        """
        (total, is_soft, is_pair, pair_value,
         dealer_value, can_double, can_split) = self._read(
            player_hand, dealer_upcard, can_double, can_split)
 
        raw = get_raw_code(total, dealer_value, is_soft=is_soft,
                           is_pair=is_pair, pair_value=pair_value)
        action = resolve_code(raw, dealer_value, total, is_soft=is_soft,
                              can_double=can_double, can_split=can_split)
        reason = _reason(action, raw, total, is_soft, is_pair,
                         pair_value, dealer_value)
 
        return {
            "action": action,
            "action_name": ACTION_NAMES[action],
            "reason": reason,
        }
 
    def evaluate(self, player_hand, dealer_upcard, player_action,
                 can_double=None, can_split=None):
        rec = self.recommend(player_hand, dealer_upcard, can_double, can_split)
        chosen = _normalize_action(player_action)
        best = rec["action"]
 
        if chosen == best:
            explanation = f"Good move — that's the optimal play. {rec['reason']}"
        else:
            explanation = (
                f"Not the best play here. The optimal move is to "
                f"{rec['action_name'].lower()}: {rec['reason']}"
            )
 
        return {
            "optimal": chosen == best,
            "player_action": chosen,
            "best_action": best,
            "best_action_name": rec["action_name"],
            "explanation": explanation,
        }
 
 
# ---------------------------------------------------------------------------
# Self-test: a spread of scenarios + a couple of evaluate() examples.
# Run with:  python -m backend.ai.advise
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from backend.game.blackjack.card import Card
    from backend.game.blackjack.hand import Hand
 
    def hand(*pairs):
        h = Hand()
        for suit, rank in pairs:
            h.add_card(Card(suit, rank))
        return h
 
    advisor = Advisor()
 
    print("=== Recommendations ===\n")
    scenarios = [
        ("Hard 16 vs 10", hand(("Spades", "10"), ("Hearts", "6")), Card("Clubs", "10")),
        ("Hard 16 vs 6",  hand(("Spades", "10"), ("Hearts", "6")), Card("Clubs", "6")),
        ("Hard 12 vs 2",  hand(("Spades", "7"), ("Hearts", "5")),  Card("Clubs", "2")),
        ("Hard 12 vs 4",  hand(("Spades", "7"), ("Hearts", "5")),  Card("Clubs", "4")),
        ("Hard 11 vs 6",  hand(("Spades", "6"), ("Hearts", "5")),  Card("Clubs", "6")),
        ("Hard 9 vs 3",   hand(("Spades", "5"), ("Hearts", "4")),  Card("Clubs", "3")),
        ("Soft 18 vs 3",  hand(("Spades", "Ace"), ("Hearts", "7")), Card("Clubs", "3")),
        ("Soft 18 vs 9",  hand(("Spades", "Ace"), ("Hearts", "7")), Card("Clubs", "9")),
        ("Soft 13 vs 5",  hand(("Spades", "Ace"), ("Hearts", "2")), Card("Clubs", "5")),
        ("Pair 8s vs 10", hand(("Spades", "8"), ("Hearts", "8")),  Card("Clubs", "10")),
        ("Pair A,A vs 5", hand(("Spades", "Ace"), ("Hearts", "Ace")), Card("Clubs", "5")),
        ("Pair 10s vs 6", hand(("Spades", "10"), ("Hearts", "10")), Card("Clubs", "6")),
        ("Pair 9s vs 7",  hand(("Spades", "9"), ("Hearts", "9")),  Card("Clubs", "7")),
        ("Hard 20 vs A",  hand(("Spades", "10"), ("Hearts", "10")), Card("Clubs", "Ace")),
    ]
    for label, ph, up in scenarios:
        rec = advisor.recommend(ph, up)
        print(f"{label:16} player {str(ph):24} dealer {up.short_name():4} "
              f"-> {rec['action_name']}")
        print(f"                 {rec['reason']}\n")
 
    print("=== evaluate() examples ===\n")
    ph = hand(("Spades", "10"), ("Hearts", "6"))  # hard 16
    print("Player stood on 16 vs dealer 10:")
    print("  " + advisor.evaluate(ph, Card("Clubs", "10"), "stand")["explanation"] + "\n")
    print("Player hit 16 vs dealer 10:")
    print("  " + advisor.evaluate(ph, Card("Clubs", "10"), "hit")["explanation"] + "\n")
 
    # ---- assertions against well-known basic-strategy answers ----
    def best(ph, up, **kw):
        return advisor.recommend(ph, up, **kw)["action"]
 
    assert best(hand(("Spades", "10"), ("Hearts", "6")), Card("Clubs", "10")) == 'H'
    assert best(hand(("Spades", "10"), ("Hearts", "6")), Card("Clubs", "6")) == 'S'
    assert best(hand(("Spades", "7"), ("Hearts", "5")), Card("Clubs", "2")) == 'H'
    assert best(hand(("Spades", "7"), ("Hearts", "5")), Card("Clubs", "4")) == 'S'
    assert best(hand(("Spades", "6"), ("Hearts", "5")), Card("Clubs", "6")) == 'D'
    assert best(hand(("Spades", "6"), ("Hearts", "5")), Card("Clubs", "6"),
                can_double=False) == 'H'
    assert best(hand(("Spades", "5"), ("Hearts", "4")), Card("Clubs", "3")) == 'D'
    assert best(hand(("Spades", "5"), ("Hearts", "4")), Card("Clubs", "2")) == 'H'
    assert best(hand(("Spades", "Ace"), ("Hearts", "7")), Card("Clubs", "3")) == 'D'
    assert best(hand(("Spades", "Ace"), ("Hearts", "7")), Card("Clubs", "9")) == 'H'
    assert best(hand(("Spades", "Ace"), ("Hearts", "7")), Card("Clubs", "2")) == 'S'
    assert best(hand(("Spades", "Ace"), ("Hearts", "2")), Card("Clubs", "5")) == 'D'
    assert best(hand(("Spades", "8"), ("Hearts", "8")), Card("Clubs", "10")) == 'P'
    assert best(hand(("Spades", "Ace"), ("Hearts", "Ace")), Card("Clubs", "5")) == 'P'
    assert best(hand(("Spades", "Ace"), ("Hearts", "Ace")), Card("Clubs", "5"),
                can_split=False) == 'H'
    assert best(hand(("Spades", "10"), ("Hearts", "10")), Card("Clubs", "6")) == 'S'
    assert best(hand(("Spades", "5"), ("Hearts", "5")), Card("Clubs", "6")) == 'D'
    assert best(hand(("Spades", "5"), ("Hearts", "5")), Card("Clubs", "10")) == 'H'
    assert best(hand(("Spades", "9"), ("Hearts", "9")), Card("Clubs", "7")) == 'S'
    assert best(hand(("Spades", "9"), ("Hearts", "9")), Card("Clubs", "6")) == 'P'
    assert best(hand(("Spades", "9"), ("Hearts", "9")), Card("Clubs", "10")) == 'S'
    assert best(hand(("Spades", "10"), ("Hearts", "10")), Card("Clubs", "Ace")) == 'S'
    print("All advise.py self-checks passed.")