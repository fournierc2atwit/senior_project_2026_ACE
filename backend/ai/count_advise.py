from backend.ai.advise import Advisor
from backend.ai.counting import (
    HI_LO_VALUES,
    get_deviation,
    should_take_insurance,
    recommend_bet,
    bet_units,
    estimated_edge,
    INSURANCE_INDEX,
)

_ACTION_NAMES = {'H': 'Hit', 'S': 'Stand', 'D': 'Double Down', 'P': 'Split'}
OVERBET_GAP = 4

_ACTION_ALIASES = {
    'h': 'H', 'hit': 'H',
    's': 'S', 'stand': 'S', 'stay': 'S',
    'd': 'D', 'double': 'D', 'double down': 'D', 'doubledown': 'D', 'dd': 'D',
    'p': 'P', 'split': 'P',
}

_TAG_LABELS = {
    +1: "Low cards",
    0:  "Neutral cards",
    -1: "High cards",
}

_TAG_MEANINGS = {
    +1: ("Good for you when they leave. Every low card dealt out means the shoe "
         "that is left holds a higher share of tens and Aces."),
    0:  ("No effect either way. Sevens, eights and nines are close enough to "
         "neutral that Hi-Lo ignores them."),
    -1: ("These are the cards you want still in the shoe. Tens and Aces make "
         "blackjacks, which pay 3:2, and they bust the dealer's stiff hands."),
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


def _rc(running_count):
    if isinstance(running_count, float) and not running_count.is_integer():
        return f"{running_count:+.1f}"
    return f"{int(running_count):+d}"


def _tag(value):
    return "0" if value == 0 else f"{value:+d}"


def _rank_short(rank):
    return {"Jack": "J", "Queen": "Q", "King": "K", "Ace": "A"}.get(rank, rank)


def _rank_span(ranks):
    if len(ranks) > 2 and all(r.isdigit() for r in ranks):
        values = [int(r) for r in ranks]
        if values == list(range(values[0], values[0] + len(values))):
            return f"{values[0]}-{values[-1]}"
    return ", ".join(_rank_short(r) for r in ranks)


def _card_name(card):
    namer = getattr(card, "short_name", None)
    if callable(namer):
        return namer()
    return str(getattr(card, "rank", card))


def count_legend(system=None):
    system = system or HI_LO_VALUES

    grouped = {}
    for rank, tag in system.items():
        grouped.setdefault(tag, []).append(rank)

    groups = []
    for tag in sorted(grouped, reverse=True):      # +1, 0, -1
        ranks = grouped[tag]
        groups.append({
            "tag": tag,
            "tag_display": _tag(tag),
            "label": _TAG_LABELS.get(tag, f"Tag {_tag(tag)}"),
            "ranks": ranks,
            "ranks_display": _rank_span(ranks),
            "meaning": _TAG_MEANINGS.get(tag, ""),
        })

    return {
        "system": "Hi-Lo",
        "groups": groups,
        "explanation": (
            "Hi-Lo tracks the balance of high and low cards still to come. Every "
            "card you see gets a tag, and you keep a running total. Low cards are "
            "+1 because once they are gone the rest of the shoe is richer in tens "
            "and Aces, which is good for you: more blackjacks at 3:2, and more "
            "dealer busts on stiff hands. High cards are -1 for the opposite "
            "reason. The tags cancel out to zero across a full deck, which is "
            "what makes the count meaningful rather than just drifting."
        ),
    }


def explain_card(card):
    rank = getattr(card, "rank", None)
    if rank not in HI_LO_VALUES:
        return {"card": _card_name(card), "tag": 0, "explanation": ""}

    tag = HI_LO_VALUES[rank]
    name = _card_name(card)

    if tag > 0:
        why = (f"{name} is a low card, so it counts {_tag(tag)}. Dealing it out "
               f"leaves the shoe richer in tens and Aces.")
    elif tag < 0:
        why = (f"{name} is a high card, so it counts {_tag(tag)}. That is one "
               f"less ten or Ace left for you.")
    else:
        why = f"{name} is neutral in Hi-Lo, so it counts 0 and the count holds."

    return {"card": name, "rank": rank, "tag": tag,
            "tag_display": _tag(tag), "explanation": why}


def explain_cards(cards, running_before=None, count_face_down=False):
    cards = list(cards or [])

    breakdown = []
    hidden = []
    delta = 0

    for card in cards:
        rank = getattr(card, "rank", None)
        visible = getattr(card, "face_up", True) or count_face_down

        if rank not in HI_LO_VALUES:
            continue

        tag = HI_LO_VALUES[rank]
        entry = {
            "card": _card_name(card),
            "rank": rank,
            "tag": tag,
            "tag_display": _tag(tag),
            "counted": bool(visible),
        }
        if visible:
            delta += tag
            breakdown.append(entry)
        else:
            hidden.append(entry)

    result = {
        "cards": breakdown + hidden,
        "counted": breakdown,
        "hidden": hidden,
        "delta": delta,
        "delta_display": _tag(delta),
        "running_before": running_before,
        "running_after": (running_before + delta) if running_before is not None else None,
    }

    if not breakdown and not hidden:
        result["explanation"] = "No cards to count yet."
        return result

    if not breakdown:
        result["explanation"] = (
            "Nothing to count yet -- the only card on the table is face down. "
            "You add it to the count when it is turned over, not before."
        )
        return result

    listing = ", ".join(f"{e['card']} {e['tag_display']}" for e in breakdown)

    if delta == 0:
        movement = "they cancel out, so the running count does not move"
    elif delta > 0:
        movement = f"that is a net {_tag(delta)} to the running count"
    else:
        movement = f"that is a net {_tag(delta)} on the running count"

    sentence = f"{listing}. Adding those up, {movement}"

    if running_before is not None:
        after = running_before + delta
        if delta == 0:
            sentence += f" -- it stays at {_rc(after)}."
        else:
            sentence += f", moving it from {_rc(running_before)} to {_rc(after)}."
    else:
        sentence += "."

    if hidden:
        names = ", ".join(e["card"] for e in hidden)
        sentence += (
            f" The dealer's hole card is still face down, so it is not counted "
            f"yet -- add it when it is turned over."
            if len(hidden) == 1 else
            f" {names} are still face down, so they are not counted yet."
        )

    result["explanation"] = sentence
    return result

def explain_true_count(running_count, decks_remaining, true_count=None):
    if decks_remaining is None or decks_remaining <= 0:
        return ""

    if true_count is None:
        true_count = running_count / decks_remaining

    return (
        f"That {_tc(true_count)} is your running count of {_rc(running_count)} "
        f"divided by the {decks_remaining:.1f} decks still left to play. The "
        f"division is the whole point: {_rc(running_count)} spread across six "
        f"decks is barely an edge, but the same {_rc(running_count)} with one "
        f"deck left is a big one, because those extra high cards are packed "
        f"into far fewer cards."
    )


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
                f"enough tens left to make it pay, insurance only becomes a good bet "
                f"once the true count reaches +{INSURANCE_INDEX}.")
        return {"offered": True, "take": take, "explanation": explanation}

    def betting_advice(self, true_count, running_count=None, decks_remaining=None, explain_dilution=False):
        units, amount = recommend_bet(true_count, unit=self.unit,
                                      max_units=self.max_units,
                                      spread_start=self.spread_start)
        edge = estimated_edge(true_count)

        can_show_math = running_count is not None and decks_remaining not in (None, 0)

        naive_units = (bet_units(running_count, max_units=self.max_units,
                                 spread_start=self.spread_start)
                       if can_show_math else units)
        division_matters = (explain_dilution and can_show_math
                            and naive_units >= units + OVERBET_GAP)

        show_math = can_show_math and (units > 1 or division_matters)

        if units == 1:
            explanation = (
                f"The true count is {_tc(true_count)}, so you have no real edge "
                f"(around {edge:+.1f}%). Bet the minimum — 1 unit (${amount}) — and "
                f"wait for the count to climb before committing more.")
            if show_math:
                explanation += (
                    f" Your running count of {_rc(running_count)} looks strong on its "
                    f"own, but with {decks_remaining:.1f} decks still in the shoe it "
                    f"only works out to {_tc(true_count)}. Those extra high cards are "
                    f"spread too thin to bet into yet -- this division is exactly what "
                    f"stops a big running count from fooling you early in a shoe."
                )
        else:
            explanation = (
                f"The true count is {_tc(true_count)}, tilting the shoe in your favor "
                f"by about {edge:+.1f}%. Raise to {units} units (${amount}) to put more "
                f"money out while you hold the advantage.")
            if show_math:
                explanation += " " + explain_true_count(
                    running_count, decks_remaining, true_count)

        return {"units": units, "amount": amount,
                "edge_percent": round(edge, 2), "explanation": explanation,
                "running_count": running_count,
                "decks_remaining": (round(decks_remaining, 2)
                                    if decks_remaining is not None else None),
                "true_count": round(true_count, 2),
                "shows_true_count_math": bool(show_math)}

    def count_status(self, running_count, decks_remaining,
                     last_cards=None, running_before=None, include_legend=True,
                     explain_dilution=False):
        decks = decks_remaining if decks_remaining and decks_remaining > 0 else None
        true_count = (running_count / decks) if decks else 0.0

        status = {
            "running_count": running_count,
            "running_count_display": _rc(running_count),
            "true_count": round(true_count, 2),
            "true_count_display": _tc(true_count),
            "decks_remaining": round(decks_remaining, 2) if decks_remaining else 0,
            "betting": self.betting_advice(true_count, running_count, decks_remaining,
                                           explain_dilution=explain_dilution),
        }

        if include_legend:
            status["legend"] = count_legend()

        if last_cards:
            status["last_deal"] = explain_cards(last_cards, running_before=running_before)

        return status


def _deviation_reason(dev, total, dealer_value, true_count, is_pair):
    action = dev['action']
    index = dev['index']
    d_label = "Ace" if dealer_value == 11 else str(dealer_value)

    if action == 'S':   # stand where basic would hit
        return (f"The true count is {_tc(true_count)} (index {index}), so a lot of "
                f"high cards are still in the shoe. That makes your next card more "
                f"likely to bust this stiff {total}, and it makes the dealer more "
                f"likely to bust too, so you should stand on a hand you'd normally hit.")

    if action == 'H':   # hit where basic would stand
        return (f"The true count is {_tc(true_count)} (index {index}), meaning the "
                f"shoe is rich in low cards. Your stiff {total} is less likely to bust "
                f"on the next card and the dealer is less likely to bust on theirs, so "
                f"you hit a hand you'd normally stand on.")

    if action == 'D':   # double where basic would hit
        return (f"The true count is {_tc(true_count)} (index {index}), so the next "
                f"card is likely to be a ten, turning your {total} into a strong "
                f"total against the dealer's {d_label}. You double to get more money "
                f"out while the odds favor you (and you take just one card).")

    if action == 'P':   # split tens
        return (f"Advanced play: normally you never break up a 20, but at a true count "
                f"of {_tc(true_count)} (index {index}) the dealer's weak {d_label} "
                f"plus all the tens left make two hands each starting with a ten worth "
                f"more than standing on 20. This is high-variance, most casual players "
                f"skip it.")

    return ""


# ---------------------------------------------------------------------------
# Self-test — run with:  python -m backend.ai.count_advise
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from backend.game.blackjack.card import Card
    from backend.game.blackjack.hand import Hand
    from backend.ai.counting import CardCounter

    def hand(*pairs):
        h = Hand()
        for suit, rank in pairs:
            h.add_card(Card(suit, rank))
        return h

    adv = CountAdvisor(unit=10)

    print("=== The legend the HUD was missing ===\n")
    legend = count_legend()
    for g in legend["groups"]:
        print(f"  {g['tag_display']:>3}  {g['ranks_display']:<16} {g['label']}")
    print(f"\n  {legend['explanation']}\n")

    print("=== What the cards just dealt did to the count ===\n")
    deal = [Card("Hearts", "5"), Card("Spades", "King"),
            Card("Diamonds", "7"), Card("Clubs", "3")]
    e = explain_cards(deal, running_before=2)
    print(f"  {e['explanation']}\n")

    print("=== Same deal, but the dealer's hole card is face down ===\n")
    with_hole = [Card("Hearts", "5"), Card("Spades", "King"),
                 Card("Clubs", "Ace", face_up=False)]
    e = explain_cards(with_hole, running_before=2)
    print(f"  {e['explanation']}\n")

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

    print("=== Betting: when is the true-count math shown? ===\n")
    cases = [
        ("quiet -- no edge, no raise, no formula",      2,  5.0),
        ("RC looks big but decks dilute it (opt-in)",   6,  6.0),
        ("the count has earned a raise",               10,  4.0),
        ("late shoe, same RC, much bigger bet",         6,  1.5),
    ]
    for label, rc, decks in cases:
        tc = rc / decks
        b = adv.betting_advice(tc, running_count=rc, decks_remaining=decks)
        shown = "MATH SHOWN" if b["shows_true_count_math"] else "quiet"
        print(f"  RC {rc:+}, {decks} decks -> TC {tc:+.1f} -> "
              f"{b['units']} unit(s), {shown}")
        print(f"    {b['explanation']}\n")

    print("=== evaluate() example ===")
    e = adv.evaluate(h16, Card("Clubs", "10"), "hit", 2.0)
    print("  Player hit 16 vs 10 at TC +2:")
    print("  " + e["explanation"] + "\n")

    print("=== End-to-end with a live CardCounter ===")
    counter = CardCounter(num_decks=6)
    counter.count_cards(deal)
    print(f"  After dealing {[c.short_name() for c in deal]}: {counter.status()}")
    status = adv.count_status(counter.running_count, counter.decks_remaining(),
                              last_cards=deal, running_before=0)
    print(f"  {status['last_deal']['explanation']}")
    print(f"  {status['betting']['explanation']}\n")

    # ---- assertions: existing behaviour must be unchanged ----
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

    # ---- legend ----
    tags = {g["tag"]: g for g in count_legend()["groups"]}
    assert set(tags) == {1, 0, -1}
    assert tags[1]["ranks_display"] == "2-6"
    assert tags[0]["ranks_display"] == "7-9"
    assert tags[-1]["ranks_display"] == "10, J, Q, K, A"
    # Groups must be derived from HI_LO_VALUES, not hardcoded, so that a change
    # to the count system flows through instead of silently going stale.
    assert sum(len(g["ranks"]) for g in tags.values()) == len(HI_LO_VALUES)

    # ---- per-card tags ----
    assert explain_card(Card("Hearts", "5"))["tag"] == 1
    assert explain_card(Card("Hearts", "8"))["tag"] == 0
    assert explain_card(Card("Hearts", "King"))["tag"] == -1
    assert explain_card(Card("Hearts", "Ace"))["tag"] == -1
    assert "0" == explain_card(Card("Hearts", "8"))["tag_display"]   # not "+0"

    # ---- the deal breakdown ----
    e = explain_cards([Card("Hearts", "5"), Card("Spades", "King")], running_before=3)
    assert e["delta"] == 0 and e["running_after"] == 3
    e = explain_cards([Card("Hearts", "5"), Card("Clubs", "3")], running_before=3)
    assert e["delta"] == 2 and e["running_after"] == 5
    assert "+3 to +5" in e["explanation"], e["explanation"]
    e = explain_cards([Card("Hearts", "King"), Card("Clubs", "Ace")], running_before=0)
    assert e["delta"] == -2 and e["running_after"] == -2

    # A face-down card must NOT be counted: a real counter cannot see it.
    hole = Card("Clubs", "Ace", face_up=False)
    e = explain_cards([Card("Hearts", "5"), hole], running_before=0)
    assert e["delta"] == 1, e["delta"]          # the Ace's -1 is excluded
    assert len(e["hidden"]) == 1
    assert "face down" in e["explanation"]
    # ...unless the caller explicitly opts in (e.g. replaying a finished hand).
    assert explain_cards([Card("Hearts", "5"), hole], count_face_down=True)["delta"] == 0
    # Nothing but a hole card means nothing to count.
    assert explain_cards([hole])["delta"] == 0
    assert explain_cards([])["delta"] == 0

    # ---- the gating rule: by default TC math appears only on a bet increase --
    quiet = adv.betting_advice(0.4, running_count=2, decks_remaining=5.0)
    assert quiet["units"] == 1
    assert quiet["shows_true_count_math"] is False
    assert "divided by" not in quiet["explanation"]

    raised = adv.betting_advice(2.5, running_count=10, decks_remaining=4.0)
    assert raised["units"] > 1
    assert raised["shows_true_count_math"] is True
    assert "divided by" in raised["explanation"]

    # Big RC, early shoe. No raise, so by DEFAULT this stays quiet -- otherwise
    # it fires on roughly a third of all hands and stops being worth reading.
    tempting = adv.betting_advice(1.0, running_count=6, decks_remaining=6.0)
    assert tempting["units"] == 1
    assert tempting["shows_true_count_math"] is False
    # Opt in and it becomes a teaching moment instead.
    taught = adv.betting_advice(1.0, running_count=6, decks_remaining=6.0,
                                explain_dilution=True)
    assert taught["shows_true_count_math"] is True
    assert "spread too thin" in taught["explanation"]
    # ...but only for a genuine overbet. A trivial RC must stay quiet even then.
    assert adv.betting_advice(0.4, running_count=2, decks_remaining=5.0,
                              explain_dilution=True)["shows_true_count_math"] is False

    # Same running count, late shoe: now it is a real raise, so it shows either way.
    late = adv.betting_advice(4.0, running_count=6, decks_remaining=1.5)
    assert late["units"] > 1 and late["shows_true_count_math"] is True

    # Callers that pass only a true count must still work, and stay quiet.
    legacy = adv.betting_advice(3.0)
    assert legacy["units"] == 3 and legacy["shows_true_count_math"] is False

    # ---- the HUD payload ----
    st = adv.count_status(6, 1.5, last_cards=[Card("Hearts", "5")], running_before=5)
    assert st["true_count"] == 4.0
    assert st["running_count_display"] == "+6"
    assert st["true_count_display"] == "+4.0"
    assert "legend" in st and "last_deal" in st and "betting" in st
    # A freshly shuffled shoe must not divide by zero.
    assert adv.count_status(0, 0)["true_count"] == 0.0

    print("All count_advise.py self-checks passed.")