from backend.ai.roulette_odds import (
    BET_SPECS,
    VALID_BET_TYPES,
    compare_bets,
    expected_loss,
    expected_spins_until_broke,
    expected_value,
    house_edge,
    martingale_analysis,
    payout_ratio,
    probability_of_no_win,
    std_dev,
    streak_probability,
    win_probability,
)
 
HEAVY_BET_FRACTION = 0.25
RECKLESS_BET_FRACTION = 0.50
 
STREAK_NOTICE = 4
 
_RISK_BANDS = [
    (1.10, "low",     "a slow grind — small swings, frequent small wins"),
    (2.00, "medium",  "a moderate ride — you'll lose more often than you win, but wins pay double"),
    (float("inf"), "extreme", "a lottery ticket — you'll lose ~37 of every 38 spins"),
]
 
 
def _risk_band(bet_type):
    sd = std_dev(bet_type, 1)
    for ceiling, name, blurb in _RISK_BANDS:
        if sd < ceiling:
            return name, blurb
    return "extreme", ""
 
 
def _pct(x):
    return f"{x * 100:.2f}%"
 
 
def _bet_label(bet_type, bet_value):
    if bet_type == "straight":
        return f"number {bet_value}"
    if bet_type == "dozen":
        return {1: "1st dozen (1-12)", 2: "2nd dozen (13-24)",
                3: "3rd dozen (25-36)"}.get(bet_value, f"dozen {bet_value}")
    return str(bet_value)
 
def _would_have_won(spin, bet_type, bet_value):
    if bet_type == "straight":
        return spin.get("number") == bet_value
    if bet_type == "color":
        return spin.get("color") == bet_value
    if bet_type == "parity":
        if bet_value == "odd":
            return bool(spin.get("is_odd"))
        if bet_value == "even":
            return bool(spin.get("is_even"))
        return False
    if bet_type == "dozen":
        return spin.get("dozen") == bet_value
    return False
 
 
def _current_streak(history, bet_type, bet_value):
    if not history:
        return 0, False
 
    latest = _would_have_won(history[-1], bet_type, bet_value)
    length = 0
    for spin in reversed(history):
        if _would_have_won(spin, bet_type, bet_value) != latest:
            break
        length += 1
    return length, latest
 
 
def _detect_chasing(history, amount):
    if not history:
        return None
 
    last = history[-1]
    last_amount = last.get("amount", 0)
    if last.get("won") or last_amount <= 0:
        return None
    if amount < last_amount * 2:
        return None
 
    losses = 0
    ladder_base = last_amount
    for spin in reversed(history):
        if spin.get("won"):
            break
        losses += 1
        ladder_base = spin.get("amount", ladder_base)
 
    return {
        "last_amount": last_amount,
        "consecutive_losses": losses,
        "ladder_base": ladder_base,
    }
 
 
class RouletteAdvisor:
    def __init__(self, heavy_fraction=HEAVY_BET_FRACTION,
                 reckless_fraction=RECKLESS_BET_FRACTION):
        self.heavy_fraction = heavy_fraction
        self.reckless_fraction = reckless_fraction
 
    def _bankroll_warning(self, chips, amount):
        if chips <= 0 or amount <= 0:
            return None
        fraction = amount / chips
 
        if fraction >= self.reckless_fraction:
            return {
                "code": "bankroll_reckless",
                "severity": "high",
                "message": (
                    f"That's {_pct(fraction)} of everything you have on one spin. "
                    f"A stack this size can't absorb a normal losing run — two bad "
                    f"spins and you're done. Smaller bets don't improve your odds, "
                    f"but they buy you enough spins for the odds to mean anything."
                ),
            }
        if fraction >= self.heavy_fraction:
            return {
                "code": "bankroll_heavy",
                "severity": "medium",
                "message": (
                    f"This is {_pct(fraction)} of your stack on a single spin. "
                    f"That's a short session — at this size you get roughly "
                    f"{expected_spins_until_broke(chips, amount):.0f} spins before "
                    f"the edge grinds you out."
                ),
            }
        return None
 
    def _streak_warning(self, history, bet_type, bet_value):
        length, was_winning = _current_streak(history, bet_type, bet_value)
        if length < STREAK_NOTICE:
            return None
 
        p = win_probability(bet_type)
        label = _bet_label(bet_type, bet_value)
        up_front = streak_probability(bet_type, length) if was_winning else \
            probability_of_no_win(bet_type, length)
 
        if was_winning:
            return {
                "code": "hot_hand",
                "severity": "medium",
                "message": (
                    f"{label} has hit {length} spins running, and it's tempting to "
                    f"call it hot. Before the run started, {length} in a row was a "
                    f"{_pct(up_front)} shot — but that's already happened. The wheel "
                    f"doesn't know. Your odds on the next spin are {_pct(p)}, the "
                    f"same as they were on the very first spin of the night."
                ),
            }
 
        return {
            "code": "gamblers_fallacy",
            "severity": "medium",
            "message": (
                f"{label} has missed {length} spins in a row, so it feels overdue. "
                f"It isn't. A drought that long was a {_pct(up_front)} shot before "
                f"it began, but the wheel has no memory of it — there's no mechanism "
                f"that makes a pocket 'catch up'. Your odds next spin are {_pct(p)}, "
                f"exactly what they always were."
            ),
        }
 
    def _chase_warning(self, history, chips, amount, bet_type):
        chase = _detect_chasing(history, amount)
        if not chase:
            return None
 
        losses = chase["consecutive_losses"]
        base = max(chase["ladder_base"], 1)
 
        model_type = bet_type if payout_ratio(bet_type) == 1 else "color"
        m = martingale_analysis(chips + amount, base, model_type)
 
        msg = (
            f"You've lost {losses} in a row and just doubled your bet to ${amount}. "
            f"That's the Martingale, and it's the most seductive losing system in the "
            f"casino. "
        )
        if m["affordable"]:
            msg += (
                f"It works right up until it doesn't: with this stack you can only "
                f"afford {m['steps']} more doublings. You'll claw back a small win "
                f"about {_pct(m['win_probability'])} of the time — and about "
                f"{_pct(m['bust_probability'])} of the time you'll lose "
                f"${m['max_loss']:,} in one ladder, wiping out every small win you "
                f"banked. The expected value is still exactly -5.26%. Doubling moves "
                f"the loss around; it never removes it."
            )
        else:
            msg += (
                f"Your stack can't even fund the next double, which means the system "
                f"has already failed — that's how it always ends. The edge is still "
                f"-5.26%, no matter the bet size."
            )
 
        return {"code": "chasing_losses", "severity": "high", "message": msg}
 
    def recommend(self, chips, amount, bet_type, bet_value, history=None):
        if bet_type not in VALID_BET_TYPES:
            raise ValueError(
                f"Unknown bet type {bet_type!r}. Use one of: {sorted(VALID_BET_TYPES)}"
            )
 
        history = history or []
        p = win_probability(bet_type)
        ratio = payout_ratio(bet_type)
        ev = expected_value(bet_type, amount)
        risk, risk_blurb = _risk_band(bet_type)
        label = _bet_label(bet_type, bet_value)
 
        warnings = [w for w in (
            self._chase_warning(history, chips, amount, bet_type),
            self._streak_warning(history, bet_type, bet_value),
            self._bankroll_warning(chips, amount),
        ) if w]
 
        verdicts = {
            "color":    "Even-money grind",
            "parity":   "Even-money grind",
            "dozen":    "Middle ground",
            "straight": "Long shot",
        }
        verdict = verdicts[bet_type]
        if any(w["severity"] == "high" for w in warnings):
            verdict = "Careful"
 
        explanation = (
            f"{label.capitalize()} pays {ratio}:1 and hits {_pct(p)} of the time. "
            f"Expected result: {ev:+.2f} chips per spin — because like every other "
            f"bet on this wheel, it hands the house 5.26%. Your pick changes the "
            f"ride, not the odds: this one is {risk_blurb}."
        )
 
        lesson = (
            f"Here's the part most players never learn: the two green pockets "
            f"(0 and 00) are the entire house edge, and they tax every bet equally. "
            f"Straight-up, red/black, odd/even, dozens — all of them return exactly "
            f"-5.26%. There is no 'smart' bet in roulette, and no betting system can "
            f"manufacture one, because adding negative-EV bets together only ever "
            f"produces a bigger negative. What you're really choosing is volatility: "
            f"${amount} on {label} swings about ±${std_dev(bet_type, amount):.0f} per "
            f"spin, and at this size the edge costs you about "
            f"${expected_loss(amount):.2f} every time you play."
        )
 
        return {
            "verdict": verdict,
            "explanation": explanation,
            "lesson": lesson,
            "warnings": warnings,
            "bet_type": bet_type,
            "bet_value": bet_value,
            "payout": f"{ratio}:1",
            "win_probability": round(p, 4),
            "win_percent": round(p * 100, 2),
            "house_edge_percent": round(house_edge(bet_type) * 100, 2),
            "expected_value": round(ev, 2),
            "volatility": risk,
            "std_dev": round(std_dev(bet_type, amount), 2),
            "spins_of_bankroll": (
                round(expected_spins_until_broke(chips, amount))
                if chips > 0 and amount > 0 else 0
            ),
        }
 
    def evaluate(self, result, chips_before=None):
        won = bool(result.get("won"))
        bet_type = result.get("bet_type")
        amount = result.get("amount", 0)
        payout = result.get("payout", 0)
        number = result.get("number")
 
        if bet_type not in VALID_BET_TYPES:
            return {"explanation": "No advice available for this bet."}
 
        p = win_probability(bet_type)
 
        if won:
            explanation = (
                f"{number} comes in — you win ${payout:,}. Worth saying plainly "
                f"though: that was a {_pct(p)} shot that happened to land, not a "
                f"good decision paying off. The same bet placed again is still "
                f"worth {expected_value(bet_type, amount):+.2f} chips. Winning "
                f"doesn't make a negative-EV bet positive; it just makes it feel "
                f"that way, which is exactly how casinos stay in business."
            )
        else:
            explanation = (
                f"{number} — no good this time. Nothing went wrong: this bet loses "
                f"{_pct(1 - p)} of the time by design, and a run of losses is the "
                f"normal texture of the game, not a sign that anything is 'due'. "
                f"The next spin is a fresh {_pct(p)}, independent of this one."
            )
 
        return {
            "won": won,
            "explanation": explanation,
            "expected_value": round(expected_value(bet_type, amount), 2),
            "win_probability": round(p, 4),
        }
 
    def compare(self, amount=100):
        rows = compare_bets(amount)
        for row in rows:
            row["house_edge_percent"] = round(row["house_edge"] * 100, 2)
            row["win_percent"] = round(row["win_probability"] * 100, 2)
            row["expected_value"] = round(row["expected_value"], 2)
            row["std_dev"] = round(row["std_dev"], 2)
            row["volatility"] = _risk_band(row["bet_type"])[0]
        return {
            "bets": rows,
            "takeaway": (
                "Every bet on the wheel returns exactly -5.26%. The payout and the "
                "hit rate move in perfect lockstep to keep it that way — 35:1 at "
                "1-in-38, 1:1 at 18-in-38. Choosing a bet chooses your volatility, "
                "never your edge."
            ),
        }
 
 
# ---------------------------------------------------------------------------
# Self-test — run with:  python -m backend.ai.roulette_advise
# ---------------------------------------------------------------------------
if __name__ == "__main__":
 
    def spin(number, color, dozen=None, is_odd=False, is_even=False,
             amount=50, won=False):
        return {"number": number, "color": color, "dozen": dozen,
                "is_odd": is_odd, "is_even": is_even,
                "amount": amount, "won": won}
 
    adv = RouletteAdvisor()
 
    codes = lambda r: {w["code"] for w in r["warnings"]}
 
    print("=== Same $100, four bets ===\n")
    for bt, bv in (("color", "red"), ("parity", "odd"),
                   ("dozen", 2), ("straight", 17)):
        r = adv.recommend(1000, 100, bt, bv)
        print(f"[{r['verdict']}] {bt} on {bv}")
        print(f"  {r['explanation']}\n")
 
    print("=== Gambler's fallacy: red after 6 blacks (flat $100 bets) ===\n")
    # Flat stake throughout, so ONLY the fallacy warning should fire.
    blacks = [spin(n, "black", amount=100, won=False) for n in (2, 4, 6, 8, 10, 11)]
    r = adv.recommend(1000, 100, "color", "red", history=blacks)
    for w in r["warnings"]:
        print(f"  [{w['code']}] {w['message']}\n")
 
    print("=== Hot-hand: betting red again after red hit 4 straight ===\n")
    # The player was ON red, so these are wins — no chasing, just a hot streak.
    reds = [spin(n, "red", amount=100, won=True) for n in (1, 3, 5, 7)]
    r = adv.recommend(1000, 100, "color", "red", history=reds)
    for w in r["warnings"]:
        print(f"  [{w['code']}] {w['message']}\n")
 
    print("=== Chasing: Martingale ladder after 3 losses ===\n")
    ladder = [
        spin(2, "black", amount=50, won=False),
        spin(4, "black", amount=100, won=False),
        spin(6, "black", amount=200, won=False),
    ]
    r = adv.recommend(1000, 400, "color", "red", history=ladder)
    for w in r["warnings"]:
        print(f"  [{w['code']}] {w['message']}\n")
 
    print("=== Post-spin: a WINNING straight bet ===\n")
    e = adv.evaluate({"won": True, "bet_type": "straight", "bet_value": 17,
                      "amount": 100, "payout": 3500, "number": 17})
    print(f"  {e['explanation']}\n")
 
    print("=== The comparison table ===\n")
    table = adv.compare(100)
    print(f"  {'bet':10}{'pays':>7}{'hits':>9}{'edge':>9}{'swing':>9}")
    for row in table["bets"]:
        print(f"  {row['bet_type']:10}{row['payout']:>6}:1"
              f"{row['win_percent']:>8.1f}%"
              f"{row['house_edge_percent']:>8.2f}%"
              f"{row['std_dev']:>9.0f}")
    print(f"\n  {table['takeaway']}\n")
 
    # ---- assertions ----
    # The advisor must never claim one bet beats another.
    edges = {adv.recommend(1000, 100, bt, bv)["house_edge_percent"]
             for bt, bv in (("color", "red"), ("parity", "odd"),
                            ("dozen", 1), ("straight", 7))}
    assert edges == {5.26}, edges
 
    # Volatility must be the thing that separates them.
    assert adv.recommend(1000, 100, "color", "red")["volatility"] == "low"
    assert adv.recommend(1000, 100, "dozen", 1)["volatility"] == "medium"
    assert adv.recommend(1000, 100, "straight", 7)["volatility"] == "extreme"
 
    # Fallacy detection fires on a drought — and ONLY that, when the stake is
    # flat. A player calmly flat-betting through a cold run is not chasing.
    flat_loss_run = codes(adv.recommend(1000, 100, "color", "red", history=blacks))
    assert flat_loss_run == {"gamblers_fallacy"}, flat_loss_run
    # ...and on a hot streak...
    assert "hot_hand" in codes(
        adv.recommend(1000, 100, "color", "red", history=reds))
    # ...and not on a short, unremarkable history.
    assert not codes(adv.recommend(1000, 50, "color", "red",
                                   history=[spin(2, "black", amount=50)]))
 
    # Chasing fires only when the stake actually doubles after a loss.
    assert "chasing_losses" in codes(
        adv.recommend(1000, 400, "color", "red", history=ladder))
    # Same losing ladder, but the player holds their stake steady -> not chasing.
    assert "chasing_losses" not in codes(
        adv.recommend(1000, 200, "color", "red", history=ladder))
    # A double after a WIN is not chasing either.
    won_last = [spin(1, "red", amount=50, won=True)]
    assert "chasing_losses" not in codes(
        adv.recommend(1000, 100, "color", "red", history=won_last))
    # The ladder base must be read from the run, not from history[0], so that a
    # capped/truncated history can't corrupt the Martingale numbers.
    assert _detect_chasing(ladder, 400)["ladder_base"] == 50
    assert _detect_chasing(ladder[1:], 400)["ladder_base"] == 100
 
    # Bankroll warnings scale with stake.
    assert "bankroll_heavy" in codes(adv.recommend(400, 100, "color", "red"))
    assert "bankroll_reckless" in codes(adv.recommend(150, 100, "color", "red"))
    assert not codes(adv.recommend(5000, 100, "color", "red"))
 
    # A win must NOT be reported as a good decision.
    win_eval = adv.evaluate({"won": True, "bet_type": "straight", "bet_value": 7,
                             "amount": 100, "payout": 3500, "number": 7})
    assert win_eval["expected_value"] < 0
 
    # Streak logic must read the right property per bet type.
    odds_history = [spin(n, "black", is_odd=True) for n in (11, 13, 15, 17)]
    assert _current_streak(odds_history, "parity", "odd") == (4, True)
    assert _current_streak(odds_history, "parity", "even") == (4, False)
 
    print("All roulette_advise.py self-checks passed.")