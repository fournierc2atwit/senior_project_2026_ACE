from ai.advise import Advisor
from ai.counting import (
    get_deviation,
    should_take_insurance,
    recommend_bet,
    estimated_edge,
    INSURANCE_INDEX,
)

_ACTION_NAMES = {'H': 'Hit', 'S': 'Stand', 'D': 'Double Down', 'P': 'Split'}

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


def _tc(true_count):
    return f"{true_count:+.1f}"


def _deviation_reason(dev, total, dealer_value, true_count, is_pair):
    action = dev['action']
    index = dev['index']
    d_label = "Ace" if dealer_value == 11 else str(dealer_value)

    if action == 'S':   # stand where basic would hit
        return (f"The true count is {_tc(true_count)} (index {index}), so a lot of "
                f"high cards are still in the shoe. That makes your next card more "
                f"likely to bust this stiff {total}, and it makes the dealer more "
                f"likely to bust too — so you stand on a hand you'd normally hit.")

    if action == 'H':   # hit where basic would stand
        return (f"The true count is {_tc(true_count)} (index {index}), meaning the "
                f"shoe is rich in low cards. Your stiff {total} is less likely to bust "
                f"on the next card and the dealer is less likely to bust on theirs, so "
                f"you hit a hand you'd normally stand on.")

    if action == 'D':   # double where basic would hit
        return (f"The true count is {_tc(true_count)} (index {index}), so the next "
                f"card is likely to be a ten — turning your {total} into a strong "
                f"total against the dealer's {d_label}. You double to get more money "
                f"out while the odds favor you (and you take just one card).")

    if action == 'P':   # split tens
        return (f"Advanced play: normally you never break up a 20, but at a true count "
                f"of {_tc(true_count)} (index {index}) the dealer's weak {d_label} "
                f"plus all the tens left make two hands each starting with a ten worth "
                f"more than standing on 20. This is high-variance — most casual players "
                f"skip it.")

    return ""


class CountAdvisor:
    def __init__(self, unit=10, max_units=8, spread_start=2, basic_advisor=None):
        self.unit = unit
        self.max_units = max_units
        self.spread_start = spread_start
        self.basic = basic_advisor or Advisor()

    def _read(self, player_hand, dealer_upcard, can_double, can_split):
        total = player_hand.get_value()
        is_soft = player_hand.is_soft()
        two_cards = player_hand.card_count() == 2

        is_rank_pair = player_hand.is_pair()
        is_ten_pair = two_cards and all(c.get_value() == 10 for c in player_hand.cards)
        is_pair = is_rank_pair or is_ten_pair
        if is_ten_pair:
            pair_value = 10
        elif is_rank_pair:
            pair_value = player_hand.cards[0].get_value()
        else:
            pair_value = None

        dealer_value = dealer_upcard.get_value()
        if can_double is None:
            can_double = two_cards
        if can_split is None:
            can_split = is_pair
        return total, is_soft, is_pair, pair_value, dealer_value, can_double, can_split

    def recommend(self, player_hand, dealer_upcard, true_count,
                  can_double=None, can_split=None):
        (total, is_soft, is_pair, pair_value,
         dealer_value, can_double, can_split) = self._read(
            player_hand, dealer_upcard, can_double, can_split)

        basic = self.basic.recommend(player_hand, dealer_upcard,
                                      can_double=can_double, can_split=can_split)

        dev = get_deviation(total, dealer_value, true_count, basic['action'],
                            is_soft=is_soft, is_pair=is_pair, pair_value=pair_value,
                            can_double=can_double, can_split=can_split)

        if dev:
            action = dev['action']
            reason = _deviation_reason(dev, total, dealer_value, true_count, is_pair)
            is_deviation = True
        else:
            action = basic['action']
            reason = ("The count doesn't change the play here, so stick with basic "
                      "strategy: " + basic['reason'])
            is_deviation = False

        return {
            "action": action,
            "action_name": _ACTION_NAMES[action],
            "reason": reason,
            "is_deviation": is_deviation,
            "basic_action": basic['action'],
            "basic_action_name": basic['action_name'],
            "true_count": round(true_count, 2),
        }

    def evaluate(self, player_hand, dealer_upcard, player_action, true_count,
                 can_double=None, can_split=None):
        rec = self.recommend(player_hand, dealer_upcard, true_count,
                             can_double=can_double, can_split=can_split)
        chosen = _normalize_action(player_action)
        best = rec["action"]

        if chosen == best:
            if rec["is_deviation"]:
                explanation = (f"Nice — that's the correct count deviation. {rec['reason']}")
            else:
                explanation = f"Good move — that's the optimal play. {rec['reason']}"
        else:
            lead = "Not the best play for this count. "
            if rec["is_deviation"]:
                lead += (f"This is one of the spots where the count matters: basic "
                         f"strategy says {rec['basic_action_name'].lower()}, but you "
                         f"should {rec['action_name'].lower()} here. ")
            else:
                lead += f"The optimal move is to {rec['action_name'].lower()}: "
            explanation = lead + rec["reason"]

        return {
            "optimal": chosen == best,
            "player_action": chosen,
            "best_action": best,
            "best_action_name": rec["action_name"],
            "is_deviation": rec["is_deviation"],
            "explanation": explanation,
        }

    def insurance(self, dealer_upcard, true_count):
        take = should_take_insurance(dealer_upcard.get_value(), true_count)
        if take is None:
            return {"offered": False, "take": False,
                    "explanation": "Insurance is only offered when the dealer shows an Ace."}
        if take:
            explanation = (
                f"Take insurance. At a true count of {_tc(true_count)}, enough tens "
                f"remain that the dealer is unusually likely to have a ten in the hole "
                f"for blackjack, which flips insurance into a profitable bet.")
        else:
            explanation = (
                f"Decline insurance. At a true count of {_tc(true_count)} there aren't "
                f"enough tens left to make it pay — insurance only becomes a good bet "
                f"once the true count reaches +{INSURANCE_INDEX}.")
        return {"offered": True, "take": take, "explanation": explanation}

    def betting_advice(self, true_count):
        units, amount = recommend_bet(true_count, unit=self.unit,
                                      max_units=self.max_units,
                                      spread_start=self.spread_start)
        edge = estimated_edge(true_count)
        if units == 1:
            explanation = (
                f"The true count is {_tc(true_count)}, so you have no real edge "
                f"(around {edge:+.1f}%). Bet the minimum — 1 unit (${amount}) — and "
                f"wait for the count to climb before committing more.")
        else:
            explanation = (
                f"The true count is {_tc(true_count)}, tilting the shoe in your favor "
                f"by about {edge:+.1f}%. Raise to {units} units (${amount}) to put more "
                f"money out while you hold the advantage.")
        return {"units": units, "amount": amount,
                "edge_percent": round(edge, 2), "explanation": explanation}


# ---------------------------------------------------------------------------
# Self-test — run with:  python -m backend.ai.count_advise
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from backend.game.card import Card
    from backend.game.hand import Hand
    from backend.ai.counting import CardCounter

    def hand(*pairs):
        h = Hand()
        for suit, rank in pairs:
            h.add_card(Card(suit, rank))
        return h

    adv = CountAdvisor(unit=10)

    print("=== Count-aware recommendations ===\n")
    h16 = hand(("Spades", "10"), ("Hearts", "6"))   # hard 16
    for tc in (-2, 0, 4):
        r = adv.recommend(h16, Card("Clubs", "10"), tc)
        flag = "  <-- DEVIATION" if r["is_deviation"] else ""
        print(f"16 vs 10  @ TC {tc:+}: {r['action_name']}{flag}")
        print(f"   {r['reason']}\n")

    h11 = hand(("Spades", "6"), ("Hearts", "5"))     # 11
    r = adv.recommend(h11, Card("Clubs", "Ace"), 1)
    print(f"11 vs A   @ TC +1: {r['action_name']}  "
          f"(basic was {r['basic_action_name']})")
    print(f"   {r['reason']}\n")

    tens = hand(("Spades", "10"), ("Hearts", "King"))  # 20, pair of tens
    r = adv.recommend(tens, Card("Clubs", "6"), 4)
    print(f"10,10 vs 6 @ TC +4: {r['action_name']}  "
          f"(basic was {r['basic_action_name']})")
    print(f"   {r['reason']}\n")

    print("=== Insurance ===")
    print("  " + adv.insurance(Card("Clubs", "Ace"), 3.0)["explanation"])
    print("  " + adv.insurance(Card("Clubs", "Ace"), 1.0)["explanation"], "\n")

    print("=== Betting ===")
    for tc in (0.5, 2.0, 5.0):
        print("  " + adv.betting_advice(tc)["explanation"])
    print()

    print("=== evaluate() example ===")
    # Player hits 16 vs 10 at a +2 count (should have stood)
    e = adv.evaluate(h16, Card("Clubs", "10"), "hit", 2.0)
    print("  Player hit 16 vs 10 at TC +2:")
    print("  " + e["explanation"] + "\n")

    print("=== End-to-end with a live CardCounter ===")
    counter = CardCounter(num_decks=6)
    counter.running_count, counter.cards_seen = 8, 104   # 8 / 4 decks left = TC +2
    tc = counter.true_count()
    print(f"  Counter: {counter.status()}")
    print("  " + adv.betting_advice(tc)["explanation"] + "\n")

    # ---- assertions against published Hi-Lo answers ----
    def act(ph, up, tc, **kw):
        return adv.recommend(ph, up, tc, **kw)["action"]

    assert act(h16, Card("Clubs", "10"), 0.0) == 'S'      # 16v10 stand at >= 0
    assert act(h16, Card("Clubs", "10"), -1.0) == 'H'     # below index -> basic hit
    assert act(hand(("Spades", "10"), ("Hearts", "5")), Card("Clubs", "10"), 4.0) == 'S'  # 15v10 @ +4
    assert act(hand(("Spades", "7"), ("Hearts", "5")), Card("Clubs", "3"), 2.0) == 'S'    # 12v3 @ +2
    assert act(hand(("Spades", "8"), ("Hearts", "4")), Card("Clubs", "4"), 0.0) == 'H'    # 12v4 @ <=0
    assert act(hand(("Spades", "8"), ("Hearts", "4")), Card("Clubs", "4"), 1.0) == 'S'    # back to basic
    assert act(h11, Card("Clubs", "Ace"), 1.0) == 'D'                                     # 11vA @ +1
    assert act(h11, Card("Clubs", "Ace"), 1.0, can_double=False) == 'H'                   # can't double
    assert act(tens, Card("Clubs", "6"), 4.0) == 'P'                                      # split tens @ +4
    assert act(tens, Card("Clubs", "6"), 3.0) == 'S'                                      # below index -> stand
    # an 8,8 (also 16) vs 10 should still SPLIT, not pick up the 16v10 deviation
    assert act(hand(("Spades", "8"), ("Hearts", "8")), Card("Clubs", "10"), 5.0) == 'P'
    print("All count_advise.py self-checks passed.")